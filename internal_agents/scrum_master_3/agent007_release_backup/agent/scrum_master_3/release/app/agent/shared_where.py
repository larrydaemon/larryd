"""HIS PLACES: his one settings file (schemas/settings.json), loaded once, and every path he reads, named there (reads)."""
import json
import os

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # his app: agent/, web/, static/, schemas/
ROOT = OFFICE = os.path.dirname(APP)   # the office: app/ and instance/
SCHEMAS = os.path.join(APP, 'schemas')
SETTINGS_FILE = ORDERS_FILE = SPRINT_FILE = os.path.join(SCHEMAS, 'settings.json')   # his orders and his sprint list are keys of it
WORDS_FILE, ROUTES_FILE, ROWS_FILE = (os.path.join(SCHEMAS, f) for f in ('words.json', 'routes.json', 'rows.json'))
INSTANCE = os.path.abspath(os.path.expanduser(os.environ.get('SCRUM_MASTER_INSTANCE') or os.path.join(OFFICE, 'instance')))
REPORTS_FILE = os.path.abspath(os.path.expanduser(os.environ.get('SCRUM_MASTER_REPORTS') or os.path.join(SCHEMAS, 'reports.json')))   # every report he allows (a check's own: $SCRUM_MASTER_REPORTS)
with open(REPORTS_FILE, encoding='utf-8') as _fh:
    REPORTS_BOOK = json.load(_fh)
LOGS = os.path.abspath(os.path.expanduser(os.environ.get('SCRUM_MASTER_LOGS') or REPORTS_BOOK['logs']))   # his own logs, named once in reports.json
REPORTS = {r['name']: os.path.expanduser(r['path'].replace('{logs}', LOGS)) for r in REPORTS_BOOK['reports']}   # every report path, by its name
with open(SETTINGS_FILE, encoding='utf-8') as _fh:
    _text = _fh.read()
SCRATCH = os.path.expanduser(os.environ.get('SCRUM_SCRATCH') or json.loads(_text)['scratch'])   # his one scratch folder
for _word, _place in (('{app}', APP), ('{schemas}', SCHEMAS), ('{instance}', INSTANCE), ('{hands}', os.path.join(APP, 'agent')), ('{scratch}', SCRATCH)):
    _text = _text.replace('"' + _word, '"' + _place)   # a value that begins with one of his places, filled in
SETTINGS = json.loads(_text)
PATHS = {k: os.path.expanduser(v) for k, v in SETTINGS['reads'].items() if not k.endswith('about')}
WORKSPACE = PATHS['workspace']


def path(name, *parts):
    """a place he reads, by its name in settings.json reads (and a file below it)"""
    return os.path.join(PATHS[name], *parts)


def report(name, *fill):
    """a report he reads, by its name in reports.json, the ONLY place a report is named; each glob part filled in order"""
    if any(not f or os.sep in f or f in ('.', '..') for f in fill):
        raise ValueError(f'not one name: {fill!r}')
    parts, fill = REPORTS[name].split(os.sep), list(fill)
    return os.sep.join(fill.pop(0) if fill and any(c in p for c in '*?[') else p for p in parts)
