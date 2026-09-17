"""Exact money helpers for the normalized EUR-only demonstration schema."""

from decimal import Decimal
import re


# A normalized signed amount with exactly two decimal places and <= 12 digits.
EUR_AMOUNT = re.compile(r"[+-]?(?:0|[1-9][0-9]{0,11})\.[0-9]{2}\Z")


def parse_eur(value: str) -> int:
    """Return integer cents; reject floats, exponents, commas and sub-cent values."""
    if not isinstance(value, str) or not EUR_AMOUNT.fullmatch(value):
        raise ValueError("Expected a normalized EUR string such as '250.00'.")
    return int(Decimal(value) * 100)


def format_eur(cents: int) -> str:
    """Format integer cents without converting through a binary float."""
    if type(cents) is not int:
        raise ValueError("Expected integer cents.")
    return f"EUR {Decimal(cents) / 100:,.2f}"
