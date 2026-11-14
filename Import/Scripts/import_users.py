"""Import Salesforce Users from Import/Data/Users.csv; dry-run by default.

Salesforce User records (not Contacts) appear as Task owners in Assigned To.
Explicit --profile-id is required to avoid guessing access privileges.
"""
import argparse
import csv
import sys
import urllib.error
from pathlib import Path
from salesforce_client import Salesforce, fail

DATA = Path(__file__).resolve().parents[1] / 'Data' / 'Users.csv'
REQUIRED = ('Username', 'Email', 'LastName', 'Alias', 'CommunityNickname')
DEFAULTS = {
    'TimeZoneSidKey': 'Asia/Jerusalem',
    'LocaleSidKey': 'en_US',
    'EmailEncodingKey': 'UTF-8',
    'LanguageLocaleKey': 'en_US',
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-org', required=True)
    parser.add_argument('--profile-id', required=True, help='Existing Salesforce Profile ID to assign')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--file', type=Path, default=DATA)
    args = parser.parse_args()
    if not args.file.is_file():
        fail(f'Missing CSV: {args.file}. Create a CSV with columns: {", ".join(REQUIRED)}')
    with args.file.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or any(k not in reader.fieldnames for k in REQUIRED):
            fail(f'CSV must include: {", ".join(REQUIRED)}')
        rows = list(reader)
    if not rows:
        fail('Users CSV is empty')
    usernames = []
    for i, row in enumerate(rows, 2):
        if any(not (row.get(k) or '').strip() for k in REQUIRED):
            fail(f'Row {i}: missing required field')
        alias = row['Alias'].strip()
        if len(alias) > 8:
            fail(f'Row {i}: Alias must be at most 8 characters')
        usernames.append(row['Username'].strip().casefold())
    if len(set(usernames)) != len(usernames):
        fail('Duplicate Username values in CSV')
    nicknames = [row['CommunityNickname'].strip().casefold() for row in rows]
    if len(set(nicknames)) != len(nicknames):
        fail('Duplicate CommunityNickname values in CSV')
    sf = Salesforce(args.target_org)
    describe = sf.request('GET', 'sobjects/User/describe')
    if not describe.get('createable'):
        fail('User object is not createable in this org')
    fields = {f['name']: f for f in describe['fields']}
    for field in REQUIRED + tuple(DEFAULTS):
        if field not in fields or not fields[field].get('createable'):
            fail(f'User field unavailable for creation: {field}')
    for i, row in enumerate(rows, 2):
        for field, value in row.items():
            if not field or not value or not value.strip():
                continue
            if field == 'ProfileId':
                fail('ProfileId must be selected with --profile-id, not CSV')
            meta = fields.get(field)
            if not meta or not meta.get('createable') or meta.get('type') == 'boolean':
                fail(f'Row {i}: unsupported CSV field: {field}')
            if meta.get('length') and len(value.strip()) > meta['length']:
                fail(f'Row {i}: {field} exceeds maximum length {meta["length"]}')
            options = [p['value'] for p in meta.get('picklistValues', []) if p.get('active')]
            if options and value.strip() not in options:
                fail(f'Row {i}: {field} value is not an active picklist option')
    for field, value in DEFAULTS.items():
        options = [p['value'] for p in fields[field].get('picklistValues', []) if p.get('active')]
        if options and value not in options:
            fail(f'Default {field}={value} not valid in this org')
    profile_id = args.profile_id.strip()
    if not (len(profile_id) in (15, 18) and profile_id.isalnum()):
        fail('Invalid --profile-id format')
    profile = sf.query("SELECT Id, Name FROM Profile WHERE Id = '" + profile_id + "'")
    if len(profile) != 1:
        fail('Profile not found in target org')
    license_rows = sf.query("SELECT Id, Name, TotalLicenses, UsedLicenses FROM UserLicense")
    license_by_id = {row['Id']: row for row in license_rows}
    profiles = sf.query("SELECT Id, Name, UserLicenseId FROM Profile WHERE Id = '" + profile_id + "'")
    license_info = license_by_id.get(profiles[0].get('UserLicenseId')) if profiles else None
    if license_info:
        available = license_info['TotalLicenses'] - license_info['UsedLicenses']
        print(f"License: {license_info['Name']} | total={license_info['TotalLicenses']} used={license_info['UsedLicenses']} available={available}")
    else:
        available = None
        print('WARNING: could not determine available licenses for selected profile')
    existing = {}
    for user in sf.query('SELECT Id, Username, Email, LastName, IsActive FROM User'):
        existing[user['Username'].strip().casefold()] = user
    plan = []
    for row in rows:
        username = row['Username'].strip()
        old = existing.get(username.casefold())
        if old and (old['Email'].strip().casefold() != row['Email'].strip().casefold()
                    or old['LastName'].strip().casefold() != row['LastName'].strip().casefold()):
            fail(f'Existing User {username}: Email or LastName mismatch; no changes made')
        if old and not old.get('IsActive'):
            fail(f'Existing User {username} is inactive and cannot receive Tasks')
        plan.append((row, old))
    print(f'Target: {sf.username} | Org ID: {sf.org_id} | Profile: {profile[0]["Name"]}')
    print(f'Users: existing={sum(bool(old) for _, old in plan)}, to create={sum(not old for _, old in plan)}')
    new_count = sum(not old for _, old in plan)
    if available is not None and new_count > available:
        fail(f'Insufficient available licenses: need {new_count}, available {available}')
    if not args.apply:
        print('DRY RUN: no changes made. Use --apply to create missing users.')
        return
    created = 0
    for row, old in plan:
        if old:
            continue
        values = {k: v.strip() for k, v in row.items()
                  if k and v is not None and v.strip() and k != 'ProfileId'}
        values.update({k: values.get(k, default) for k, default in DEFAULTS.items()})
        values['ProfileId'] = profile_id
        values['IsActive'] = True
        sf.create('User', values)
        created += 1
    print(f'Completed: created={created}; existing users unchanged.')

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, urllib.error.URLError) as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(1)
