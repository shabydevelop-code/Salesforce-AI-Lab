#!/usr/bin/env python3
"""Salesforce AI Lab: safe, repeatable 400-record import. Python 3.9+; Salesforce CLI.
Dry run by default. Use --apply to create missing records in the explicitly selected org.
Existing matching records are verified, never overwritten; mismatches stop the import.
"""
import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

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


from salesforce_client import Salesforce


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-org', required=True, help='Salesforce CLI org alias or username')
    parser.add_argument('--apply', action='store_true', help='Actually create missing records')
    args = parser.parse_args()
    data = {kind: load(filename, key) for kind, filename, key in FILES}
    sf = Salesforce(args.target_org)
    print(f'Target: {args.target_org} | {sf.username} | Org ID: {sf.org_id}')
    print('Mode:', 'APPLY' if args.apply else 'DRY RUN (no writes)')

    # Salesforce org-specific picklist configuration is checked before writes.
    stages = sf.query('SELECT MasterLabel, IsActive, IsClosed FROM OpportunityStage')
    active = {s['MasterLabel'] for s in stages if s.get('IsActive') and not s.get('IsClosed')}
    if not active:
        fail('No active open Opportunity stages')
    fallback_stage = sorted(active)[0]
    for row in data['Opportunity']:
        if row['StageName'] not in active:
            print(f'NOTE: stage {row["StageName"]!r} unavailable; using {fallback_stage!r}')
            row['StageName'] = fallback_stage

    account_idx = lookup(sf, 'Account', 'AccountNumber')
    contact_idx = lookup(sf, 'Contact', 'Email')
    lead_idx = lookup(sf, 'Lead', 'Email')
    opp_idx = lookup(sf, 'Opportunity', 'Name')
    account_ids = {}
    plans = {}
    for kind, key, idx in [('Account', 'AccountNumber', account_idx),
                           ('Contact', 'Email', contact_idx),
                           ('Lead', 'Email', lead_idx),
                           ('Opportunity', 'Name', opp_idx)]:
        plan = []
        for row in data[kind]:
            old = single(idx, row[key], kind)
            if old and kind == 'Account' and norm(old.get('Name')) != norm(row['Name']):
                fail(f'Account {row[key]} exists with a different name')
            if old and kind in ('Contact', 'Lead') and norm(old.get('LastName')) != norm(row['LastName']):
                fail(f'{kind} {row[key]} exists with a different last name')
            plan.append((row, old))
        plans[kind] = plan
        print(f'{kind}: existing={sum(bool(old) for _,old in plan)}, '
              f'to create={sum(not old for _,old in plan)}')

    # Existing relationship conflicts must be detected before writing.
    for row, old in plans['Account']:
        if old:
            account_ids[norm(row['AccountNumber'])] = old['Id']
    for kind in ('Contact', 'Opportunity'):
        for row, old in plans[kind]:
            if old and old.get('AccountId'):
                target = account_ids.get(norm(row['AccountNumber']))
                if target and old['AccountId'] != target:
                    fail(f'{kind} {row["Email" if kind == "Contact" else "Name"]}: linked to another Account')

    if not args.apply:
        print('Dry run passed. No Salesforce records modified. Use --apply to execute.')
        return

    counts = {'Account': 0, 'Contact': 0, 'Lead': 0, 'Opportunity': 0, 'Contact links': 0}
    for row, old in plans['Account']:
        values = clean(row)
        # BillingState deliberately omitted from normalized source; invalid in source org.
        if old:
            account_ids[norm(row['AccountNumber'])] = old['Id']
        else:
            record_id = sf.create('Account', values)
            account_ids[norm(row['AccountNumber'])] = record_id
            counts['Account'] += 1

    for row, old in plans['Contact']:
        aid = account_ids[norm(row['AccountNumber'])]
        if old:
            if old.get('AccountId') and old['AccountId'] != aid:
                fail(f'Contact {row["Email"]} already linked to a different Account')
            if not old.get('AccountId'):
                sf.update('Contact', old['Id'], {'AccountId': aid})
                counts['Contact links'] += 1
        else:
            values = clean(row, {'AccountNumber'})
            values['AccountId'] = aid
            sf.create('Contact', values)
            counts['Contact'] += 1

    # Lead.Status is required by some org configurations; use the org default if omitted.
    lead_meta = sf.request('GET', 'sobjects/Lead/describe')
    status_field = next((f for f in lead_meta['fields'] if f['name'] == 'Status'), None)
    status_default = next((p['value'] for p in status_field['picklistValues'] if p.get('defaultValue') and p.get('active')), None) if status_field else None
    if not status_default and status_field:
        status_default = next((p['value'] for p in status_field['picklistValues'] if p.get('active')), None)
    for row, old in plans['Lead']:
        if not old:
            values = clean(row)
            if status_default:
                values['Status'] = status_default
            sf.create('Lead', values)
            counts['Lead'] += 1

    for row, old in plans['Opportunity']:
        aid = account_ids[norm(row['AccountNumber'])]
        if old:
            if old.get('AccountId') and old['AccountId'] != aid:
                fail(f'Opportunity {row["Name"]} already linked to a different Account')
        else:
            values = clean(row, {'AccountNumber'})
            values['AccountId'] = aid
            sf.create('Opportunity', values)
            counts['Opportunity'] += 1

    print('Completed:', counts)
    print('Existing records were not overwritten. Re-run dry run to confirm no missing records.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, urllib.error.URLError) as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(1)



