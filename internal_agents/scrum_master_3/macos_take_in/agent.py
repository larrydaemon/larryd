"""MACOS TAKE IN (SM2 agent028): the Mac app written from tonight's web code (native_generate); the iPhone take in's write serves it
when it passed in the last hours (fact written_within_hours). Dry: whether that write serves, else the command it would run."""
import datetime

import night
from night import F, last_real


def written_tonight():
    r = last_real('native_generate', [])
    try:
        at = datetime.datetime.fromisoformat(str(r.get('finished') or ''))
    except ValueError:
        return None
    return r if r.get('ok') and datetime.datetime.now(datetime.timezone.utc) - at < datetime.timedelta(hours=F('written_within_hours')) else None


def own(given, dry):
    had = written_tonight()
    if had:
        return {'skip': True, 'lines': [f"macos · take in · written tonight already ({str(had.get('finished'))[:16]}, {str(had.get('commit') or '')[:12]}): the same write serves both apps"]}
    return {'lines': [f"macos · take in · no write in the last {F('written_within_hours')} h: it writes again"]}


if __name__ == '__main__':
    night.main(own)
