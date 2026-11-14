"""Import 100 synthetic Tasks linked to existing CRM demo records.

Dry-run by default. No Salesforce Users are created or modified.
"""
import argparse
import csv
import sys
import urllib.error
from datetime import date, timedelta
from pathlib import Path

from salesforce_client import Salesforce, fail

DATA = Path(__file__).resolve().parents[1] / 'Data'
PREFIX = 'AI-LAB-TASK-'
OWNERS = ('ronen penso', 'OrgFarm EPIC')


def read_csv(name):
    with (DATA / name).open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 100:
        fail(f'{name}: expected 100 rows, got {len(rows)}')
    return rows


def unique_index(rows, key, label):
    result = {}
    for row in rows:
        value = (row.get(key) or '').strip().casefold()
        if not value or value in result:
            fail(f'{label}: missing or duplicate {key}: {value!r}')
        result[value] = row
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-org', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()

    contacts = read_csv('Contacts.csv')
    leads = read_csv('Leads.csv')
    opportunities = read_csv('Opportunities.csv')
    sf = Salesforce(args.target_org)
    print(f'Target: {sf.username} | Org ID: {sf.org_id}')
    print('Mode:', 'APPLY' if args.apply else 'DRY RUN')

    owners = sf.query("SELECT Id, Name, IsActive, UserType FROM User WHERE Name IN ('ronen penso', 'OrgFarm EPIC')")
    by_name = {}
    for owner in owners:
        by_name.setdefault(owner['Name'], []).append(owner)
    for name in OWNERS:
        matches = by_name.get(name, [])
        if len(matches) != 1 or not matches[0]['IsActive'] or matches[0]['UserType'] != 'Standard':
            fail(f'Expected exactly one active Standard User named {name!r}')
    owner_ids = [by_name[name][0]['Id'] for name in OWNERS]

    contact_emails = [r['Email'].strip().lower() for r in contacts[:50]]
    lead_emails = [r['Email'].strip().lower() for r in leads[:50]]
    opportunity_names = [r['Name'].strip() for r in opportunities[:50]]
    # Read only the exact synthetic keys, not unrelated records.
    contact_rows = sf.query("SELECT Id, Email FROM Contact WHERE Email LIKE 'contact%@example.com'")
    lead_rows = sf.query("SELECT Id, Email FROM Lead WHERE Email LIKE 'lead%@example.com'")
    opportunity_rows = sf.query("SELECT Id, Name FROM Opportunity WHERE Name LIKE 'AI-LAB-OPP-%'")
    contact_index = unique_index(contact_rows, 'Email', 'Salesforce Contact')
    lead_index = unique_index(lead_rows, 'Email', 'Salesforce Lead')
    opportunity_index = unique_index(opportunity_rows, 'Name', 'Salesforce Opportunity')

    meta = sf.request('GET', 'sobjects/Task/describe')
    fields = {field['name']: field for field in meta['fields']}
    for required in ('Subject', 'Status', 'Priority', 'OwnerId', 'WhoId', 'WhatId', 'ActivityDate', 'Description'):
        if required not in fields or not fields[required].get('createable', False):
            fail(f'Task field is not createable: {required}')
    def picklist(field_name):
        options = [v for v in fields[field_name].get('picklistValues', []) if v.get('active')]
        if not options:
            fail(f'Task {field_name}: no active picklist values')
        default = next((v['value'] for v in options if v.get('defaultValue')), None)
        return default or options[0]['value']
    status = picklist('Status')
    priority = picklist('Priority')

    existing = sf.query("SELECT Id, Subject, Description FROM Task WHERE Subject LIKE 'AI-LAB-TASK-%'")
    existing_index = {}
    for task in existing:
        subject = task.get('Subject') or ''
        if subject in existing_index:
            fail(f'Duplicate existing Task subject: {subject}')
        existing_index[subject] = task

    actions = ['Follow up with customer', 'Schedule a discovery call',
               'Review CRM requirements', 'Confirm next steps',
               'Prepare a demo']
    plans = []
    for i in range(100):
        key = f'{PREFIX}{i + 1:04d}'
        subject = key + ' | ' + actions[i % len(actions)]
        description = f'Synthetic Salesforce AI Lab task {key}. Not a real customer activity.'
        values = {
            'Subject': subject,
            'Description': description,
            'OwnerId': owner_ids[i % len(owner_ids)],
            'Status': status,
            'Priority': priority,
            'ActivityDate': (date(2026, 11, 16) + timedelta(days=(i % 35))).isoformat(),
        }
        if i < 50:
            email = contact_emails[i]
            opp_name = opportunity_names[i]
            if email not in contact_index or opp_name.casefold() not in opportunity_index:
                fail(f'{key}: missing Contact {email} or Opportunity {opp_name}')
            values['WhoId'] = contact_index[email]['Id']
            values['WhatId'] = opportunity_index[opp_name.casefold()]['Id']
        else:
            email = lead_emails[i - 50]
            if email not in lead_index:
                fail(f'{key}: missing Lead {email}')
            values['WhoId'] = lead_index[email]['Id']
        old = existing_index.get(subject)
        if old and old.get('Description') != description:
            fail(f'{key}: existing Task subject conflicts with a different Description')
        plans.append((key, values, old))

    print('Owners:', ', '.join(OWNERS))
    print(f'Task defaults: Status={status!r}, Priority={priority!r}')
    print(f'Tasks: existing={sum(bool(old) for _, _, old in plans)}, to create={sum(not old for _, _, old in plans)}')
    if not args.apply:
        print('Dry run passed. No records modified.')
        return
    created = 0
    for key, values, old in plans:
        if old:
            continue
        sf.create('Task', values)
        created += 1
    print(f'Completed: created={created}, already existing={100-created}')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, urllib.error.URLError) as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(1)
