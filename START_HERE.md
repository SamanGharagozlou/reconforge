# Tonight's setup

Keep tonight to a small, useful checkpoint. The objective is to run and understand
the first financial example before tomorrow's main session.

## 1. Open the project

Unzip `ReconForge_Starter_Kit.zip`. Open the `reconforge-starter` folder in your
editor. In the editor's terminal, confirm that this is your current directory.
On macOS, you can also type `cd ` in Terminal, drag the extracted folder into the
window, and press Return.

Check Python:

```bash
python3 --version
```

This starter targets Python 3.12 or newer. If Python is unavailable, record that
as tomorrow's first setup item; the CSV files and documentation are still readable.

## 2. Run the example and tests

```bash
python3 -m reconforge.demo
python3 -m unittest discover -s tests -v
```

Expected findings: the ledger exceeds the provider total by EUR 250.00; the
provider and bank totals agree; `evt_invoice_001` is absent from the ledger.

## 3. Inspect the evidence

Open the three CSV files under `examples/invoice_deduction` in your editor.
Find the invoice-deduction event in the provider file and confirm that it is
absent from the ledger. The final `description` column is explanatory data only.

Practice this explanation in your own words:

“The bank received the amount the provider reports. Our internal ledger is
missing a EUR 250 deduction, so the discrepancy is between the ledger and the
provider. A person still needs to review the proposed correction.”

## 4. Finish with tomorrow's starting point

- [ ] I can run the example, or have recorded the exact setup error.
- [ ] I can locate the source of the EUR 250 difference.
- [ ] I understand that the current output is produced by deterministic code.
- [ ] I have opened `docs/DAY_01.md`.

Tonight's deliverable is this runnable local foundation. Creating a GitHub
repository and publishing it is a separate next step; nothing in this archive
publishes code or contacts anybody.
