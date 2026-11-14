"""Preview deletion of the exact CRM demo CSV records; destructive apply is guarded.

Only records with matching unique keys AND matching source field values are candidates.
No Users are touched. Inspect dry run before --apply and --confirm-org-id.
"""
import argparse
import sys
import urllib.error

from import_common import FILES, load, norm, single
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Scripts'))
from salesforce_client import Salesforce, fail

ORDER = ('Opportunity', 'Contact', 'Lead', 'Account')
FIELDS = {
    'Account': ('AccountNumber', 'Name'),
    'Contact': ('Email', 'FirstName', 'LastName'),
    'Lead': ('Email', 'FirstName', 'LastName', 'Company'),
    'Opportunity': ('Name',),
}
KEYS = {kind: key for kind, _, key in FILES}


def quote(value):
    return "'" + value.replace('\\', '\\\\').replace("'", "\\'") + "'"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-org', required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--confirm-org-id', help='Required with --apply; must match the displayed Salesforce Org ID')
    args = parser.parse_args()
    if args.apply and not args.confirm_org_id:
        fail('Refusing deletion: --apply requires --confirm-org-id')
    data = {kind: load(filename, key) for kind, filename, key in FILES}
    sf = Salesforce(args.target_org)
    print(f'Target: {sf.username} | Org ID: {sf.org_id}')
    if args.apply and args.confirm_org_id != sf.org_id:
        fail('Org ID mismatch: no records deleted')
    plan = {}
    # Query by exact CSV keys, never delete based on broad prefixes or record counts.
    for kind in ORDER:
        key = KEYS[kind]
        fields = tuple(dict.fromkeys(('Id',) + FIELDS[kind] + (('AccountId',) if kind in ('Contact', 'Opportunity') else ())))
        records = []
        rows = data[kind]
        for offset in range(0, len(rows), 40):
            keys = ','.join(quote(row[key].strip()) for row in rows[offset:offset + 40])
            soql = f'SELECT {", ".join(fields)} FROM {kind} WHERE {key} IN ({keys})'
            records.extend(sf.query(soql))
        index = {}
        for record in records:
            index.setdefault(norm(record.get(key)), []).append(record)
        matched = []
        for row in rows:
            record = single(index, row[key], kind)
            if not record:
                continue
            for field in FIELDS[kind]:
                if norm(record.get(field)) != norm(row.get(field)):
                    fail(f'{kind} {row[key]}: {field} differs from CSV; refusing entire deletion')
            matched.append((row, record))
        plan[kind] = matched
        print(f'{kind}: matched {len(matched)} / {len(rows)} CSV records')
    account_ids = {norm(row['AccountNumber']): rec['Id'] for row, rec in plan['Account']}
    # Do not delete contacts/opportunities if their linked Account differs from the source.
    for kind in ('Contact', 'Opportunity'):
        for row, record in plan[kind]:
            expected = account_ids.get(norm(row['AccountNumber']))
            if not expected or record.get('AccountId') != expected:
                fail(f'{kind} {row[KEYS[kind]]}: Account relation mismatch or Account missing; refusing deletion')
    if not args.apply:
        print('DRY RUN: no records deleted. Review counts and org identity before applying.')
        print('WARNING: Salesforce may cascade-delete dependent records. Inspect related data first.')
        return
    print('WARNING: deleting matched records in dependency order; Salesforce deletion may cascade.')
    counts = {}
    for kind in ORDER:
        counts[kind] = 0
        for _, record in plan[kind]:
            sf.request('DELETE', f'sobjects/{kind}/{record["Id"]}')
            counts[kind] += 1
        print(f'{kind}: deleted {counts[kind]}')
    print('Deletion completed:', counts)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, urllib.error.URLError) as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(1)
