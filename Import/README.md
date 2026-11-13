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
