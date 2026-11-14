"""Shared CSV loading, matching and normalization for CRM imports."""
import csv
from pathlib import Path

from salesforce_client import fail

ROOT = Path(__file__).resolve().parents[1] / 'Data'
FILES = [('Account', 'Accounts.csv', 'AccountNumber'),
         ('Contact', 'Contacts.csv', 'Email'),
         ('Lead', 'Leads.csv', 'Email'),
         ('Opportunity', 'Opportunities.csv', 'Name')]


def fail(message):
    raise RuntimeError(message)


def load(name, key):
    path = ROOT / name
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if not rows or len(rows) != 100:
        fail(f'{name}: expected 100 rows; got {len(rows)}')
    keys = [(r.get(key) or '').strip().casefold() for r in rows]
    if any(not k for k in keys) or len(set(keys)) != len(keys):
        fail(f'{name}: missing or duplicate {key}')
    return rows




def norm(value):
    return str(value or '').strip().casefold()


def lookup(sf, kind, field):
    # Read all relevant records, including those that predate this dataset.
    rows = sf.query(f'SELECT Id, {field}' + (', AccountId' if kind in ('Contact', 'Opportunity') else '')
                    + (', Name' if kind == 'Account' else '')
                    + (', LastName' if kind in ('Contact', 'Lead') else '')
                    + f' FROM {kind} WHERE {field} != null')
    index = {}
    for row in rows:
        k = norm(row.get(field))
        index.setdefault(k, []).append(row)
    return index


def single(index, key, kind):
    matches = index.get(norm(key), [])
    if len(matches) > 1:
        fail(f'{kind}: ambiguous existing records for {key!r}')
    return matches[0] if matches else None


def clean(row, skip=()):
    return {k: v.strip() for k, v in row.items() if k not in skip and v is not None and v.strip()}

