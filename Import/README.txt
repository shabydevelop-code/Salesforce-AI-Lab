Salesforce AI Lab - portable import package

Requirements: Python 3.9+, Salesforce CLI (sf), an authorized target org.

From the package root:
  python Import/Scripts/import_all.py --target-org SalesforceDev
  python Import/Scripts/import_all.py --target-org SalesforceDev --apply

The first command is a read-only preview; --apply creates missing records.
Always inspect the target org, and verify org-specific validation rules, field
permissions, record types and picklists before applying. Salesforce IDs are
resolved in the target org from AccountNumber. The script never deletes records.
Existing records are not overwritten. The import is not atomic; if interrupted,
rerun the dry run and then --apply. Account and contact relationships are checked.

This package contains exactly four 100-row CSVs and one importer script.
