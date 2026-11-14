"""Import Lead records. Dry run unless --apply is specified."""
import sys
import urllib.error
from import_crm_object import run

if __name__ == '__main__':
    try:
        run('Lead')
    except (RuntimeError, OSError, ValueError, KeyError, urllib.error.URLError) as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(1)
