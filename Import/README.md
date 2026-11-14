# Salesforce Import — Commands & Troubleshooting

Quick reference for running the import tools and resolving errors encountered on Windows. This file is **not** a project status report or a description of the current implementation. Check the actual script and CLI help for supported options.

## PowerShell commands

Run from the repository root:

```powershell
cd C:\yossi\ChatGpt\Salesforce-AI-Lab
python Import\Scripts\import_accounts.py --target-org SalesforceDev
```

The command above runs in dry-run mode (no writes). To perform an import **only after reviewing the target org and dry-run output**:

```powershell
python Import\Scripts\import_accounts.py --target-org SalesforceDev --apply
```

Check the Salesforce CLI connection and org identity:

```powershell
sf org display --target-org SalesforceDev
```

Validate Python syntax after editing:

```powershell
python -m py_compile Import\Scripts\import_accounts.py
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

`salesforce_client.py` contains the shared Salesforce CLI and REST/SOQL client. Each CRM object has an independent importer; they share `import_crm_object.py` and `import_common.py`. There is no combined importer. Users require explicit Profile selection.

```powershell
python Import\Scripts\import_accounts.py --target-org SalesforceDev
python Import\Scripts\import_contacts.py --target-org SalesforceDev
python Import\Scripts\import_leads.py --target-org SalesforceDev
python Import\Scripts\import_opportunities.py --target-org SalesforceDev
```

Append `--apply` only after reviewing the dry run. Import Accounts before Contacts and Opportunities. The CRM datasets are expected to have 100 rows per CSV.

### Users for Task Assigned To > People

Create `Import/Data/Users.csv` based on the committed `Import/Templates/Users.example.csv` header. Required fields: `Username`, `Email`, `LastName`, `Alias`, `CommunityNickname`; `FirstName` is optional. Usernames must be globally unique across Salesforce orgs. Do not put passwords in the CSV.

First select a valid Profile ID in the **target** development org:

```powershell
sf data query --target-org SalesforceDev --query "SELECT Id, Name FROM Profile ORDER BY Name"
python Import\Scripts\import_users.py --target-org SalesforceDev --profile-id PROFILE_ID
python Import\Scripts\import_users.py --target-org SalesforceDev --profile-id PROFILE_ID --apply
```

The importer does not guess a Profile or license, does not overwrite existing Users, rejects mismatched or inactive existing Users, and defaults to dry run. Salesforce Developer Edition still enforces its own User limits. User creation may trigger Salesforce email notifications. User import is separate because it requires explicit Profile selection.

## Resetting the existing CRM demo dataset

The delete script uses Salesforce sObject Collections batch DELETE (up to 200 IDs per request), not Bulk API 2.0 jobs. It selects candidates by the keys and source fields in the four CSV files. It does not touch Users. It stops if a batch reports failures; after an interrupted or failed run, inspect a new dry run before retrying. It prints matched counts before any changes and requires both `--apply` and the exact target Salesforce Org ID for deletion. **Matching CSV values alone cannot prove provenance**: inspect the dry run and related records before authorizing deletion. Salesforce may cascade deletions to other dependent records.

```powershell
python Import\Tools\delete_imported_data.py --target-org SalesforceDev
# ONLY AFTER REVIEW AND EXPLICIT APPROVAL:
python Import\Tools\delete_imported_data.py --target-org SalesforceDev --apply --confirm-org-id YOUR_ORG_ID
```

Re-import in dependency order, first dry-run each script and then run it with `--apply`:

```powershell
python Import\Scripts\import_accounts.py --target-org SalesforceDev --apply
python Import\Scripts\import_contacts.py --target-org SalesforceDev --apply
python Import\Scripts\import_leads.py --target-org SalesforceDev --apply
python Import\Scripts\import_opportunities.py --target-org SalesforceDev --apply
```

Re-run each importer without `--apply` to verify all 100 source keys already exist. Do not begin new object imports until the reset and verification are complete.

## Validate User schema and available licenses

Run the read-only inspector before creating Users:

```powershell
python Import\Tools\inspect_users_schema.py --target-org SalesforceDev
```

The User importer checks CSV fields against the live User object description, validates picklist values and lengths, and checks available licenses for the selected Profile before creating active Users. Salesforce may still apply additional org-specific rules. The CSV template is a header-only example; no User records have been generated or imported. Do not run User import before selecting the intended Profile and preparing real or synthetic data with suitable email addresses.

## Script placement

`Import/Scripts/` contains operational import scripts and their shared runtime modules. `Import/Tools/` contains manual inspection and maintenance utilities, which are not part of the routine import flow. Do not place one-off diagnostics in `Scripts/`.

## Data placement

`Import/Data/` contains only CSV datasets intended for actual import. `Import/Templates/` contains example CSV schemas and blank templates; never place example files in `Data/`.

## PowerShell script lifecycle and paste safety

- Do not provide multi-line PowerShell command sequences for direct paste into the user's console: direct paste from ChatGPT has executed lines in reverse order. Single commands are acceptable.
- When multiple ordered commands are necessary, prefer one reusable, fail-fast `.ps1` runner committed to GitHub `main`, which the user retrieves with a single `git pull --ff-only origin main` and runs with one command.
- Reuse or extend an existing operational script where appropriate; do not create a new `.ps1` for every task.
- Keep scripts with ongoing operational value in their relevant permanent directory (for example `Import/Scripts/Import-All.ps1`).
- Treat one-off scripts as temporary. If a temporary script must be committed, isolate it from operational scripts, identify it as temporary, and propose removal after its purpose is complete. Do not create a `Temp` directory unless actually needed.
- Never delete or replace a retained operational script without the user's approval. Obtain approval before deleting a temporary script from the repository as well.
- Scripts that change Salesforce data must require an explicit apply action, stop immediately on errors, and preserve dependency order.
- Keep this document focused on stable commands and troubleshooting rules, not project progress or completion status.
