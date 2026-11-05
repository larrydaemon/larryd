"""TEST, on the data just synced (SM2 agent033): the newest NIGHT Web build (the Judge), iPhone build and macOS build (their walks, the
pixel compare) must have ended green on a real run (their jobs' lights, read from its workflow's records; a dry run built nothing), then
the smoke test and the look run again. No app is built here. Dry: it reads the three and names the commands it would run."""
import night
import office
from night import F


def own(given, dry):
    jobs = {j.get('data_full_name'): j for j in office.workflow(given)}
    lines = []
    for name in F('from_night'):
        j = jobs.get(name) or {}
        d = office.data_of(j)
        if office.light_of(j) != 'GREEN' or d.get('dry'):
            said = 'never run' if not j.get('data_job_last_run_at') and not d else 'dry only: it built nothing' if d.get('dry') and office.light_of(j) == 'GREEN' else str(d.get('why') or j.get('data_job_today_said') or 'not green')
            return {'lines': lines, 'why': f'the newest NIGHT {name} is not green: {said[:200]}', 'step': f'RUN {name} (that piece alone), then RUN here'}
        lines.append(f"test · NIGHT {name} · green ({j.get('data_job_last_run_at', '')[:16]})")
    return {'lines': lines}


if __name__ == '__main__':
    night.main(own)
