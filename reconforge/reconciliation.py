"""Conservative comparison of one normalized, synthetic EUR settlement batch."""

import csv
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from io import StringIO
from pathlib import Path

from .money import parse_eur


FIELDS = (
    "tenant_id", "merchant_id", "batch_id", "event_id", "event_type",
    "amount_eur", "currency", "effective_at", "description",
)
COMPONENT_TYPES = {"Capture", "Fee", "Refund", "ReserveAdjustment", "InvoiceDeduction"}
NEGATIVE_TYPES = {"Fee", "Refund", "InvoiceDeduction"}


class InputError(ValueError):
    """The supplied records are not supported or cannot be compared safely."""


@dataclass(frozen=True)
class Event:
    event_id: str
    event_type: str
    cents: int
    effective_at: str
    description: str
    scope: tuple[str, str, str, str]
    filename: str
    record_number: int
    content_hash: str

    def reference(self) -> dict:
        return {
            "file": self.filename,
            "record_number": self.record_number,
            "event_id": self.event_id,
            "sha256": self.content_hash,
        }


def load_events(path: Path, *, bank: bool = False) -> list[Event]:
    """Read one byte snapshot and validate its normalized schema and scope.

    Record numbers are one-based CSV data records, excluding the header. They
    are not physical line numbers, since quoted descriptions may contain newlines.
    """
    try:
        content = path.read_bytes()
        text = content.decode("utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise InputError(f"Cannot read UTF-8 input {path.name}: {exc}") from exc

    digest = sha256(content).hexdigest()
    reader = csv.DictReader(StringIO(text, newline=""), strict=True)
    events: list[Event] = []
    seen: set[str] = set()
    allowed_types = {"Payout"} if bank else COMPONENT_TYPES

    try:
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise InputError(f"{path.name}: headers must exactly match the fixture schema.")
        for record_number, row in enumerate(reader, 1):
            where = f"{path.name}, data record {record_number}"
            if None in row or any(row.get(name) in (None, "") for name in FIELDS):
                raise InputError(f"{where}: missing or extra fields.")
            if row["currency"] != "EUR":
                raise InputError(f"{where}: only EUR is supported by this baseline.")
            if row["event_type"] not in allowed_types:
                raise InputError(f"{where}: unsupported event type.")
            if row["event_id"] in seen:
                raise InputError(f"{where}: duplicate event ID {row['event_id']}.")
            seen.add(row["event_id"])
            try:
                cents = parse_eur(row["amount_eur"])
                timestamp = datetime.fromisoformat(row["effective_at"].replace("Z", "+00:00"))
            except ValueError as exc:
                raise InputError(f"{where}: invalid amount or timestamp.") from exc
            if timestamp.utcoffset() is None:
                raise InputError(f"{where}: timestamp must include a timezone.")
            if cents == 0:
                raise InputError(f"{where}: zero-value events are unsupported.")
            if row["event_type"] in NEGATIVE_TYPES and cents > 0:
                raise InputError(f"{where}: this fixture type must have a negative amount.")
            if row["event_type"] in {"Capture", "Payout"} and cents < 0:
                raise InputError(f"{where}: this fixture type must have a positive amount.")
            scope = tuple(row[name] for name in ("tenant_id", "merchant_id", "batch_id", "currency"))
            events.append(Event(
                event_id=row["event_id"], event_type=row["event_type"], cents=cents,
                effective_at=timestamp.isoformat(), description=row["description"],
                scope=scope, filename=path.name, record_number=record_number,
                content_hash=digest,
            ))
    except csv.Error as exc:
        raise InputError(f"{path.name}: invalid CSV.") from exc

    if not events:
        raise InputError(f"{path.name}: no data records; completeness cannot be assumed.")
    if len({event.scope for event in events}) != 1:
        raise InputError(f"{path.name}: mixed tenant, merchant, batch or currency.")
    if bank and len(events) != 1:
        raise InputError("This baseline supports exactly one bank payout per batch.")
    return events


def reconcile(directory: Path) -> dict:
    """Compare supplied files and retain unresolved event-level differences."""
    ledger = load_events(directory / "ledger_events.csv")
    provider = load_events(directory / "psp_events.csv")
    bank = load_events(directory / "bank_entries.csv", bank=True)
    if len({ledger[0].scope, provider[0].scope, bank[0].scope}) != 1:
        raise InputError("The three sources must use the same tenant, merchant, batch and currency.")

    ledger_by_id = {event.event_id: event for event in ledger}
    provider_by_id = {event.event_id: event for event in provider}
    differences = []
    for event_id in sorted(ledger_by_id.keys() | provider_by_id.keys()):
        left = ledger_by_id.get(event_id)
        right = provider_by_id.get(event_id)
        if left is None:
            kind = "provider_event_absent_from_ledger"
        elif right is None:
            kind = "ledger_event_absent_from_provider"
        elif (left.cents, left.event_type, left.effective_at) != (right.cents, right.event_type, right.effective_at):
            kind = "event_values_differ"
        else:
            continue
        differences.append({
            "kind": kind,
            "event_id": event_id,
            "ledger_amount_minor": left.cents if left else None,
            "provider_amount_minor": right.cents if right else None,
            "ledger_source": left.reference() if left else None,
            "provider_source": right.reference() if right else None,
        })

    totals = {
        "ledger": sum(event.cents for event in ledger),
        "provider": sum(event.cents for event in provider),
        "bank": sum(event.cents for event in bank),
    }
    ledger_residual = totals["ledger"] - totals["provider"]
    bank_residual = totals["provider"] - totals["bank"]
    scope = dict(zip(("tenant_id", "merchant_id", "batch_id", "currency"), ledger[0].scope))
    return {
        "schema_version": "0.0.1",
        "mode": "deterministic_fixture_comparison",
        "scope": scope,
        "totals_minor": totals,
        "comparisons": {
            "ledger_to_provider": {
                "residual_minor": ledger_residual,
                "status": "needs_review" if ledger_residual or differences else "balanced_on_supplied_events",
            },
            "provider_to_bank": {
                "residual_minor": bank_residual,
                "status": "needs_review" if bank_residual else "balanced_by_total",
            },
        },
        "event_differences": differences,
        "source_snapshots": [
            {"file": rows[0].filename, "sha256": rows[0].content_hash, "data_records": len(rows)}
            for rows in (ledger, provider, bank)
        ],
        "review_required": bool(ledger_residual or bank_residual or differences),
        "external_completeness_verified": False,
    }
