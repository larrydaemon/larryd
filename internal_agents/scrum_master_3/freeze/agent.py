"""FREEZE, RELEASE's first step (SM2 agent031): the countdown to the freeze (freeze_weeks before the swap day) and to the swap. Green while
it can be told; red once the swap day is past (the next sprint's dates are the owner's to set in agent.json). From the freeze DAY's Pick
takes only a request marked FIX. It only counts days: dry or not, nothing is run."""
import datetime

import night
import office
from night import F


def own(given, dry):
    today = office.now().date()
    swap = datetime.date.fromisoformat(F('release_day'))
    frozen = swap - datetime.timedelta(weeks=F('freeze_weeks'))
    if today > swap:
        return {'why': f'the swap day {swap:%B %d, %Y} is past: the next release has no date',
                'step': 'set release_day and freeze_weeks in its agent.json to the next sprint, then RUN here'}
    if today < frozen:
        return {'lines': [f'freeze · {(frozen - today).days} day(s) to the freeze ({frozen:%B %d}) · {(swap - today).days} to the swap ({swap:%B %d})']}
    return {'lines': [f'freeze · FROZEN since {frozen:%B %d}: DAY builds only requests marked FIX · {(swap - today).days} day(s) to the swap ({swap:%B %d})']}


if __name__ == '__main__':
    night.main(own)
