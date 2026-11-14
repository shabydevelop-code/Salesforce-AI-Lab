"""Independent CRM object import, using the same safety rules as import_all.py."""
import argparse
from salesforce_client import Salesforce, fail
from import_common import load, lookup, single, clean, norm

CONFIG = {
    'Account': ('Accounts.csv', 'AccountNumber'),
    'Contact': ('Contacts.csv', 'Email'),
    'Lead': ('Leads.csv', 'Email'),
    'Opportunity': ('Opportunities.csv', 'Name'),
}

def run(kind):
    parser = argparse.ArgumentParser(description=f'Import {kind} records into Salesforce')
    parser.add_argument('--target-org', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    filename, key = CONFIG[kind]
    rows = load(filename, key)
    sf = Salesforce(args.target_org)
    print(f'Target: {sf.username} | Org ID: {sf.org_id}')
    print('Mode:', 'APPLY' if args.apply else 'DRY RUN')
    index = lookup(sf, kind, key)
    plans = []
    for row in rows:
        old = single(index, row[key], kind)
        if old and kind == 'Account' and norm(old.get('Name')) != norm(row['Name']):
            fail(f'Account {row[key]} exists with a different name')
        if old and kind in ('Contact', 'Lead') and norm(old.get('LastName')) != norm(row['LastName']):
            fail(f'{kind} {row[key]} exists with a different last name')
        plans.append((row, old))
    account_ids = {}
    if kind in ('Contact', 'Opportunity'):
        accounts = lookup(sf, 'Account', 'AccountNumber')
        for row, old in plans:
            account = single(accounts, row['AccountNumber'], 'Account')
            if not account:
                fail(f'{kind} {row[key]}: missing Account {row["AccountNumber"]}; import Accounts first')
            account_ids[norm(row['AccountNumber'])] = account['Id']
            if old and old.get('AccountId') and old['AccountId'] != account['Id']:
                fail(f'{kind} {row[key]}: linked to another Account')
    if kind == 'Opportunity':
        stages = sf.query('SELECT MasterLabel, IsActive, IsClosed FROM OpportunityStage')
        active = {s['MasterLabel'] for s in stages if s.get('IsActive') and not s.get('IsClosed')}
        if not active:
            fail('No active open Opportunity stages')
        fallback = sorted(active)[0]
        for row, _ in plans:
            if row['StageName'] not in active:
                print(f'NOTE: stage {row["StageName"]!r} unavailable; using {fallback!r}')
                row['StageName'] = fallback
    if kind == 'Lead':
        meta = sf.request('GET', 'sobjects/Lead/describe')
        field = next((f for f in meta['fields'] if f['name'] == 'Status'), None)
        values = [p for p in field['picklistValues'] if p.get('active')] if field else []
        lead_status = next((p['value'] for p in values if p.get('defaultValue')), None)
        if not lead_status and values:
            lead_status = values[0]['value']
    print(f'{kind}: existing={sum(bool(old) for _, old in plans)}, to create={sum(not old for _, old in plans)}')
    if not args.apply:
        print('Dry run passed. No records modified.')
        return
    created, linked = 0, 0
    for row, old in plans:
        if old:
            if kind == 'Contact' and not old.get('AccountId'):
                sf.update('Contact', old['Id'], {'AccountId': account_ids[norm(row['AccountNumber'])]})
                linked += 1
            continue
        values = clean(row, {'AccountNumber'} if kind in ('Contact', 'Opportunity') else ())
        if kind in ('Contact', 'Opportunity'):
            values['AccountId'] = account_ids[norm(row['AccountNumber'])]
        if kind == 'Lead' and lead_status:
            values['Status'] = lead_status
        sf.create(kind, values)
        created += 1
    print(f'Completed: created={created}, linked={linked}')

if __name__ == '__main__':
    raise SystemExit('Run import_accounts.py, import_contacts.py, import_leads.py, or import_opportunities.py')
