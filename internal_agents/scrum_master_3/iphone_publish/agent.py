"""IPHONE PUBLISH (SM2 agent027; the owner 2026-10-31: "the next time the phone gets connected to a cable it auto publishes"): the
walked iPhone build staged for the phone, then put on it when it is on its cable at this RUN (native.transfer); not on the cable, it
stays staged and the next RUN tries again (on demand: no watcher, no clock). Red: the kept build is not ready (never walked, or walked
red). Dry: it reads the kept build, its walk and the staged record, and names what it would stage and run."""
import json
import os
import subprocess

import night
import office
from night import F, tail, ready


def staged():
    try:
        with open(F('staged'), encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


TRANSFER = "import json\nfrom core_engine import native\nlast = None\nfor e in native.transfer():\n    last = e\nprint(json.dumps(last or {}, default=str))"


def own(given, dry):
    k, why = ready('iphone')
    if why:
        return {'why': f'the kept iPhone build is not ready: {why}', 'step': 'RUN iPhone build (its clean build and walk), then RUN here'}
    before = staged()
    s = before if before.get('commit') == k['commit'] else {'commit': k['commit'], 'bundle': k['bundle'], 'made_at': k.get('made_at', ''), 'staged_at': office.stamp()}
    send = f"cd {F('tower_app')} && PYTHONPATH=. {F('python')} -c native.transfer()"
    line = f"iphone · publish · {k['commit'][:12]} (made {str(k.get('made_at'))[:16]})"
    if s.get('transferred_at'):
        return {'lines': [f"{line} · on the phone since {s['transferred_at'][:16]}"]}
    if dry:
        return {'lines': [line + ' · ready, not on the phone yet'], 'would': [f"stage {k['commit'][:12]} in {F('staged')}", send]}
    got = subprocess.run([F('python'), '-c', TRANSFER], cwd=F('tower_app'), capture_output=True, text=True, timeout=900,
                         env={**os.environ, 'PYTHONPATH': '.', 'PYTHONDONTWRITEBYTECODE': '1'})
    try:
        ev = json.loads((got.stdout or '').strip().splitlines()[-1])
    except (ValueError, IndexError):
        ev = {'why': tail(got.stdout + got.stderr) or f'it ended {got.returncode}'}
    s['looked'] = f"{office.stamp()[:16]} · " + ('on the phone' if ev.get('ok') else str(ev.get('why') or ev)[:160])
    if ev.get('ok'):
        s['transferred_at'] = office.stamp()
    os.makedirs(os.path.dirname(F('staged')), exist_ok=True)
    with open(F('staged') + '.tmp', 'w', encoding='utf-8') as fh:
        json.dump(s, fh, indent=1)
    os.replace(F('staged') + '.tmp', F('staged'))
    return {'lines': [f"{line} · " + ('on the phone now' if ev.get('ok') else f"staged, waiting for the cable ({s['looked']})")]}


if __name__ == '__main__':
    night.main(own)
