"""THE LONG-RUN PATH (the LARRYD runtime design, decisions 5, 6 and 9; the owner chose CPU only during requests): a job's
RUN never runs on a thread after the answer (an instance gets almost no CPU once it has answered). On Cloud Run it runs
as its own Cloud Run JOB execution: the service claims the run once, starts the execution and answers at once; the
execution runs the job with this same code and sends the result to the platform by a signed callback.

THE CLAIM: a run is started once across every instance: a Firestore document `job_claims/<job_key>:<run>` created with
create(), which refuses an id that exists; the start-up catch-up uses the same claim, so two new instances never start the
same queued run. On a laptop or a test the claims are kept in memory and the run goes on a thread (no CPU limit there)."""
import datetime
import json
import os
import re
import threading
import urllib.error
import urllib.request

CLAIM_DAYS = 14
RUN_KEY = re.compile(r'^[A-Za-z0-9_]{1,64}$')


class MemoryClaims:
    def __init__(self):
        self.seen, self.lock = set(), threading.Lock()

    def claim(self, job_key, run):
        with self.lock:
            if (job_key, int(run)) in self.seen:
                return False
            self.seen.add((job_key, int(run)))
            return True


class FirestoreClaims:
    def __init__(self, col=None, exists=None):
        if col is None:
            from google.cloud import firestore   # only on the server
            from google.api_core.exceptions import AlreadyExists
            col, exists = firestore.Client().collection('job_claims'), AlreadyExists
        self.col, self.exists = col, exists

    def claim(self, job_key, run):
        if not RUN_KEY.fullmatch(str(job_key)):
            raise ValueError('not a job key')
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=CLAIM_DAYS)
        try:
            self.col.document(f'{job_key}:{int(run)}').create({'expire_at': expire})
            return True
        except self.exists:
            return False


class CloudRunJobs:
    """Starts the job execution with the run's arguments (the Cloud Run Admin API, the service's own identity from the
    metadata server; no key is ever made)."""
    METADATA = 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token'

    def __init__(self, project, region, job, opener=urllib.request.urlopen):
        self.project, self.region, self.job, self.open = project, region, job, opener

    def _token(self):
        req = urllib.request.Request(self.METADATA, headers={'Metadata-Flavor': 'Google'})
        with self.open(req, timeout=5) as r:
            return json.load(r)['access_token']

    def start(self, args):
        url = f'https://run.googleapis.com/v2/projects/{self.project}/locations/{self.region}/jobs/{self.job}:run'
        body = json.dumps({'overrides': {'containerOverrides': [{'args': list(args)}]}}).encode('utf-8')
        req = urllib.request.Request(url, data=body, method='POST',
                                     headers={'Authorization': 'Bearer ' + self._token(), 'Content-Type': 'application/json'})
        with self.open(req, timeout=15) as r:
            return r.status in (200, 201, 202)


def from_environment():
    """The job starter Cloud Run names (LARRYD_JOB, GOOGLE_CLOUD_PROJECT, LARRYD_REGION), or None (a laptop)."""
    job = os.environ.get('LARRYD_JOB')
    if not job:
        return None
    return CloudRunJobs(os.environ['GOOGLE_CLOUD_PROJECT'], os.environ.get('LARRYD_REGION', 'us-central1'), job)
