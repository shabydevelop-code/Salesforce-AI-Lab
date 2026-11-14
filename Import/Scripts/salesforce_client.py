"""Shared Salesforce CLI authentication and REST/SOQL client."""
import json
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request


def fail(message):
    raise RuntimeError(message)


class Salesforce:
    def __init__(self, alias):
        cmd = [shutil.which('sf.cmd') or shutil.which('sf'), 'org', 'display', '--target-org', alias, '--json']
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', shell=False)
        if result.returncode:
            fail('Salesforce CLI login failed: ' + (result.stderr or result.stdout)[:500])
        payload = json.loads(result.stdout)
        if payload.get('status') != 0:
            fail('Salesforce org display failed')
        org = payload['result']
        self.url = org.get('instanceUrl', '').rstrip('/')
        token_cmd = [
            shutil.which('sf.cmd') or shutil.which('sf'),
            'org', 'auth', 'show-access-token',
            '--target-org', alias, '--json'
        ]
        token_result = subprocess.run(
            token_cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            shell=False
        )
        if token_result.returncode:
            fail('Unable to retrieve Salesforce access token')
        token_payload = json.loads(token_result.stdout)
        self.token = token_payload['result']['accessToken']
        self.username = org.get('username')
        self.org_id = org.get('id')
        if not self.url or not self.token:
            fail('Missing instanceUrl or accessToken; authorize org with sf org login web')
        self.base = self.url + '/services/data/v60.0/'

    def request(self, method, path, body=None, headers=None):
        data = json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None
        request_headers = {'Authorization': 'Bearer ' + self.token,
                           'Content-Type': 'application/json;charset=UTF-8'}
        if headers:
            request_headers.update(headers)
        req = urllib.request.Request(
            self.base + path, data=data, method=method, headers=request_headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                raw = response.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            fail(f'{method} {path.split("?")[0]}: HTTP {exc.code}: '
                 + exc.read().decode('utf-8', 'replace')[:700])

    def query(self, soql):
        path = 'query?q=' + urllib.parse.quote(soql, safe='')
        result = []
        while path:
            page = self.request('GET', path)
            result.extend(page['records'])
            next_url = page.get('nextRecordsUrl')
            path = next_url.split('/services/data/v60.0/', 1)[-1] if next_url else None
        return result

    def create(self, kind, values, allow_duplicate_save=False):
        headers = {'Sforce-Duplicate-Rule-Header': 'allowSave=true'} if allow_duplicate_save else None
        result = self.request('POST', f'sobjects/{kind}', values, headers=headers)
        if not result.get('success') or not result.get('id'):
            fail(f'{kind} create failed: {result}')
        return result['id']

    def update(self, kind, record_id, values):
        self.request('PATCH', f'sobjects/{kind}/{record_id}', values)
