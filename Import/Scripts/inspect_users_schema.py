"""Inspect the live User schema and available profiles in a Salesforce org.

Read-only. No user creation, data modification, or access-token output.
"""
import argparse
import sys
import urllib.error

from salesforce_client import Salesforce, fail


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-org', required=True)
    args = parser.parse_args()
    sf = Salesforce(args.target_org)
    info = sf.request('GET', 'sobjects/User/describe')
    fields = info.get('fields', [])
    by_name = {f['name']: f for f in fields}
    print(f'Target: {sf.username} | Org ID: {sf.org_id}')
    print('User object: createable=' + str(info.get('createable')))
    print('\nREQUIRED ON CREATE (createable, non-nillable, no default):')
    for f in fields:
        if f.get('createable') and not f.get('nillable') and not f.get('defaultedOnCreate'):
            print(f"  {f['name']} | type={f.get('type')} | length={f.get('length')}")
    print('\nCSV TEMPLATE FIELDS:')
    for name in ('Username', 'Email', 'FirstName', 'LastName', 'Alias',
                 'TimeZoneSidKey', 'LocaleSidKey', 'EmailEncodingKey',
                 'LanguageLocaleKey', 'ProfileId', 'IsActive'):
        f = by_name.get(name)
        if f is None:
            print(f'  {name}: NOT FOUND')
        else:
            print(f"  {name}: createable={f.get('createable')} required={not f.get('nillable') and not f.get('defaultedOnCreate')} type={f.get('type')} length={f.get('length')}")
            if f.get('picklistValues'):
                values = [p.get('value') for p in f['picklistValues'] if p.get('active')]
                print(f'    active values ({len(values)}): ' + ', '.join(str(v) for v in values[:30]))
    print('\nPROFILES AND LICENSES:')
    for p in sf.query('SELECT Id, Name, UserLicense.Name FROM Profile ORDER BY Name'):
        license_info = p.get('UserLicense') or {}
        print(f"  {p['Id']} | {p['Name']} | license={license_info.get('Name')}")
    print('\nACTIVE USER COUNTS BY PROFILE:')
    counts = {}
    for u in sf.query('SELECT ProfileId, IsActive FROM User'):
        if u.get('IsActive'):
            counts[u['ProfileId']] = counts.get(u['ProfileId'], 0) + 1
    for profile_id, count in sorted(counts.items()):
        print(f'  {profile_id}: {count}')
    print('\nRead-only inspection complete; no Salesforce data modified.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, urllib.error.URLError) as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(1)
