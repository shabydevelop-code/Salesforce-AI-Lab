# Salesforce Import — Commands & Troubleshooting

Quick reference for running the import tools and resolving errors encountered on Windows. This file is **not** a project status report or a description of the current implementation. Check the actual script and CLI help for supported options.

## PowerShell commands

Run from the repository root:

```powershell
cd C:\yossi\ChatGpt\Salesforce-AI-Lab
python Import\Scripts\import_all.py --target-org SalesforceDev
```

The command above runs in dry-run mode (no writes). To perform an import **only after reviewing the target org and dry-run output**:

```powershell
python Import\Scripts\import_all.py --target-org SalesforceDev --apply
```

Check the Salesforce CLI connection and org identity:

```powershell
sf org display --target-org SalesforceDev
```

Validate Python syntax after editing:

```powershell
python -m py_compile Import\Scripts\import_all.py
```

## Errors encountered and fixes

### `[WinError 2] The system cannot find the file specified`

When Python invokes Salesforce CLI through `subprocess.run(..., shell=False)`, Windows may not resolve `sf` as an executable even though PowerShell does.

Check the executable:

```powershell
Get-Command sf -All
python -c "import shutil; print(shutil.which('sf.cmd'))"
```

Use the resolved CLI executable in Python, e.g. `shutil.which('sf.cmd') or shutil.which('sf')`, rather than assuming `sf` will launch directly.

### `HTTP 401: INVALID_AUTH_HEADER`

`sf org display --json` can return a masked access token rather than a usable token. Retrieve the token programmatically using `sf org auth show-access-token --target-org <alias> --json` and pass it in the HTTP `Authorization: Bearer <token>` header. Never print, log, or commit tokens.

### `IndentationError: unexpected indent`

PowerShell text replacement can accidentally duplicate or remove Python indentation. Preserve the surrounding block indentation; then run `python -m py_compile` before execution. Avoid repeated blind string replacements.

### Salesforce CSV / Bulk API parsing errors

For CSV generation, use Python's `csv` module with consistent quoting and CRLF line endings where required by the import method. Avoid relying on PowerShell CSV output if the receiving API rejects its format.

### Invalid `BillingState` value

Salesforce orgs with restricted state/country picklists may reject free-text state values. Check the target org's permitted values; map to valid values or omit the field if it is optional.

## Git workflow

Changes are committed directly to `main` on GitHub. Update the Windows checkout using:

```powershell
git pull --ff-only origin main
```

If Git reports local changes or untracked-file conflicts, inspect them before pulling. Do not force-reset or overwrite local files.

## Modular import commands

`salesforce_client.py` contains the shared Salesforce CLI and REST/SOQL client. The existing `import_all.py` remains backward-compatible and imports the four CRM objects only (not Users). Individual object importers share `import_crm_object.py`.

```powershell
python Import\Scripts\import_accounts.py --target-org SalesforceDev
python Import\Scripts\import_contacts.py --target-org SalesforceDev
python Import\Scripts\import_leads.py --target-org SalesforceDev
python Import\Scripts\import_opportunities.py --target-org SalesforceDev
```

Append `--apply` only after reviewing the dry run. Import Accounts before Contacts and Opportunities. The CRM datasets are expected to have 100 rows per CSV.

### Users for Task Assigned To > People

Create `Import/Data/Users.csv` based on the committed `Users.example.csv` header. Required fields: `Username`, `Email`, `LastName`, `Alias`; `FirstName` is optional. Usernames must be globally unique across Salesforce orgs. Do not put passwords in the CSV.

First select a valid Profile ID in the **target** development org:

```powershell
sf data query --target-org SalesforceDev --query "SELECT Id, Name FROM Profile ORDER BY Name"
python Import\Scripts\import_users.py --target-org SalesforceDev --profile-id PROFILE_ID
python Import\Scripts\import_users.py --target-org SalesforceDev --profile-id PROFILE_ID --apply
```

The importer does not guess a Profile or license, does not overwrite existing Users, rejects mismatched or inactive existing Users, and defaults to dry run. Salesforce Developer Edition still enforces its own User limits. User creation may trigger Salesforce email notifications. Existing `import_all.py` does not invoke this importer because it requires explicit Profile selection.
