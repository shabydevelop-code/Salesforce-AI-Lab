# Salesforce AI Lab — Data Import

## Overview

This directory contains sample Salesforce data and the Python import script.

- 100 Accounts
- 100 Contacts
- 100 Leads
- 100 Opportunities

## Requirements

- Python 3
- Salesforce CLI (`sf`)
- An authenticated Salesforce org with permissions for the four objects
- Windows supported (the script resolves `sf.cmd`)

## Usage

From the repository root, run a read-only dry run:

```powershell
python Import\Scripts\import_all.py --target-org SalesforceDev
```

To write records after reviewing the dry-run results:

```powershell
python Import\Scripts\import_all.py --target-org SalesforceDev --apply
```

Replace `SalesforceDev` with the alias of the intended target org. Confirm the org identity before using `--apply`.

## Import sequence and relationships

The script processes Accounts, Contacts, Leads, and Opportunities. Contacts and Opportunities must be linked to Accounts in the **target** org; Salesforce record IDs from a different org must not be reused. The dataset uses AccountNumber as a stable Account reference.

The script attempts to detect existing records to avoid duplicates. Review matching rules and target-org validation before writing, especially in an org containing unrelated data.

## Troubleshooting

### WinError 2 on Windows

Calling `sf` via Python `subprocess.run(..., shell=False)` may fail because the installed executable is `sf.cmd`. Resolve it using `shutil.which('sf.cmd') or shutil.which('sf')`, and keep `shell=False`.

### HTTP 401 INVALID_AUTH_HEADER

`sf org display --json` may return a masked `accessToken`. The script retrieves the usable token via `sf org auth show-access-token --target-org <alias> --json`. Do not print or commit access tokens.

### IndentationError after editing Python from PowerShell

PowerShell string replacement can introduce incorrect Python indentation. Run:

```powershell
python -m py_compile Import\Scripts\import_all.py
```

before retrying the import.

### CSV and Salesforce field validation

During the original import, CSV quoting/line endings caused Bulk API parsing failures. Generating CSVs with Python's `csv` module and CRLF line endings resolved those failures. The `BillingState` field also contained values rejected by the target org's restricted state/country picklist; the import data was adjusted accordingly.

## Verified behavior

A dry run against the original development org completed successfully:

| Object | Existing | To create |
| --- | ---: | ---: |
| Account | 100 | 0 |
| Contact | 100 | 0 |
| Lead | 100 | 0 |
| Opportunity | 100 | 0 |

No records were modified. A full import into a separate empty org has **not** yet been validated.

## Security

Never commit Salesforce access tokens, credentials, CLI authentication files, or sensitive output to Git. Keep authentication and org selection external to the dataset.
