"""Import synthetic Salesforce Tasks from Import/Data/Tasks.csv; dry-run by default."""
import argparse
import csv
import sys
import urllib.error
from datetime import date
from pathlib import Path
from salesforce_client import Salesforce, fail

PATH = Path(__file__).resolve().parents[1] / 'Data' / 'Tasks.csv'
FIELDS = ('TaskKey','Subject','Description','OwnerName','Status','Priority','ActivityDate','WhoType','WhoKey','WhatType','WhatKey')

def read_tasks():
    with PATH.open(encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(FIELDS):
            fail('Tasks.csv: unexpected columns')
        rows = list(reader)
    if len(rows) != 100:
        fail(f'Tasks.csv: expected 100 rows, found {len(rows)}')
    keys, subjects = set(), set()
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            fail('Tasks.csv: malformed row')
        row.update({key: value.strip() for key,value in row.items()})
        key, subject = row['TaskKey'], row['Subject']
        if not key.startswith('AI-LAB-TASK-') or not key[12:].isdigit():
            fail(f'Invalid TaskKey: {key}')
        if not subject.startswith(key + ' | ') or not row['Description']:
            fail(f'{key}: invalid subject or description')
        if key in keys or subject.casefold() in subjects:
            fail(f'{key}: duplicate TaskKey or Subject')
        keys.add(key)
        subjects.add(subject.casefold())
        try:
            date.fromisoformat(row['ActivityDate'])
        except ValueError:
            fail(f'{key}: invalid ActivityDate')
        if row['WhoType'] not in ('Contact','Lead') or not row['WhoKey']:
            fail(f'{key}: invalid WhoType/WhoKey')
        if row['WhatType'] not in ('','Opportunity') or bool(row['WhatType']) != bool(row['WhatKey']):
            fail(f'{key}: invalid WhatType/WhatKey')
        if row['WhoType'] == 'Lead' and row['WhatType']:
            fail(f'{key}: Lead cannot have WhatId')
    return rows

def make_index(sf, query, field):
    index = {}
    for item in sf.query(query):
        key = (item.get(field) or '').strip().casefold()
        if key:
            index.setdefault(key, []).append(item['Id'])
    return index

def get_id(index, key, label):
    found = index.get(key.casefold(), [])
    if len(found) != 1:
        fail(f'{label} {key!r}: expected one match, found {len(found)}')
    return found[0]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-org', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    tasks = read_tasks()
    sf = Salesforce(args.target_org)
    print(f'Target: {sf.username} | Org ID: {sf.org_id}')
    print('Mode:', 'APPLY' if args.apply else 'DRY RUN')
    meta = sf.request('GET','sobjects/Task/describe')
    fields = {f['name']:f for f in meta['fields']}
    for name in ('Subject','Description','OwnerId','Status','Priority','ActivityDate','WhoId','WhatId'):
        if name not in fields or not fields[name].get('createable'):
            fail(f'Task field is not createable: {name}')
    for name in ('Status','Priority'):
        allowed = {p['value'] for p in fields[name]['picklistValues'] if p.get('active')}
        for row in tasks:
            if allowed and row[name] not in allowed:
                fail(f'{row["TaskKey"]}: invalid {name}: {row[name]}')
    for name in ('Subject','Description'):
        maximum = fields[name].get('length',0)
        if maximum:
            for row in tasks:
                if len(row[name]) > maximum:
                    fail(f'{row["TaskKey"]}: {name} too long')
    users = make_index(sf,"SELECT Id, Name FROM User WHERE IsActive = true AND UserType = 'Standard'",'Name')
    contacts = make_index(sf,"SELECT Id, Email FROM Contact WHERE Email LIKE 'contact%@example.com'",'Email')
    leads = make_index(sf,"SELECT Id, Email FROM Lead WHERE Email LIKE 'lead%@example.com'",'Email')
    opportunities = make_index(sf,"SELECT Id, Name FROM Opportunity WHERE Name LIKE 'AI-LAB-OPP-%'",'Name')
    existing = {}
    for record in sf.query("SELECT Id, Subject, Description FROM Task WHERE Subject LIKE 'AI-LAB-TASK-%'"):
        existing.setdefault((record.get('Subject') or '').casefold(),[]).append(record)
    plans = []
    for row in tasks:
        key = row['TaskKey']
        values = {
            'Subject':row['Subject'], 'Description':row['Description'],
            'OwnerId':get_id(users,row['OwnerName'],'User'),
            'Status':row['Status'], 'Priority':row['Priority'],
            'ActivityDate':row['ActivityDate'],
            'WhoId':get_id(contacts if row['WhoType']=='Contact' else leads,
                           row['WhoKey'],row['WhoType']),
        }
        if row['WhatType']:
            values['WhatId'] = get_id(opportunities,row['WhatKey'],'Opportunity')
        found = existing.get(row['Subject'].casefold(),[])
        if len(found)>1:
            fail(f'{key}: duplicate existing Tasks')
        old = found[0] if found else None
        if old and old.get('Description') != row['Description']:
            fail(f'{key}: conflicting existing Task')
        plans.append((values,old))
    count = sum(old is None for _,old in plans)
    print(f'Tasks: existing={len(plans)-count}, to create={count}')
    if not args.apply:
        print('Dry run passed. No records modified.')
        return
    created = 0
    for values,old in plans:
        if old is None:
            sf.create('Task',values)
            created += 1
    print(f'Completed: created={created}, already existing={len(plans)-created}')

if __name__=='__main__':
    try:
        main()
    except (RuntimeError,OSError,ValueError,KeyError,urllib.error.URLError) as exc:
        print('ERROR:',exc,file=sys.stderr)
        sys.exit(1)
