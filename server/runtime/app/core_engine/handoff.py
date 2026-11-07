"""THE HANDOFF (frost-05's ruling 2026-11-07): an input too large to go inside the ask (outside.DATA_URI_MOST) is lent to the provider
as Replicate documents for a large file, "an HTTP URL": its bytes are put, for one make only, at gs://<the lockers bucket>/handoff/<a
random token> (the existing larryd bucket: private, public access prevention enforced, uniform access; a lifecycle rule deletes
handoff/ after one day whatever happens), and the provider is given a V4 SIGNED URL for that ONE object: GET only, valid 60 minutes
(a cold boot reads its input late: flux-krea took over 180 s), never public, never listable, no key in it. The object is deleted when
the make ends, made or not (outside.Hand.make's finally). The signed URL is a secret for its hour: it goes to the provider inside the
ask and nowhere else, never to a log, a run record, an agent or an answer.

On Cloud Run there is no key file: the URL is signed through IAM Credentials (signBlob) AS the runtime's own service account, which
holds roles/iam.serviceAccountTokenCreator on ITSELF only (applied 2026-11-07, frost-05's go) and roles/storage.objectUser on the
bucket. `bucket` and `signer` may be given (a test's stand-in)."""
import datetime
import logging
import os
import re
import secrets

LOG = logging.getLogger('runtime')
PREFIX = 'handoff/'
MINUTES = 60
NAME = re.compile(r'^handoff/[0-9a-f]{32}$')


class Handoff:
    def __init__(self, bucket_name=None, bucket=None, signer=None, minutes=MINUTES):
        if bucket is None:
            from google.cloud import storage   # only on the server
            bucket = storage.Client().bucket(bucket_name)
        self.bucket, self.minutes = bucket, minutes
        self.signer = signer or self._signed

    def _signed(self, blob):
        """A V4 signed GET URL for this one blob, signed by IAM Credentials as the runtime's own account (no key file on Cloud Run)."""
        import google.auth
        from google.auth.transport import requests as auth_requests
        creds, _project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        creds.refresh(auth_requests.Request())
        return blob.generate_signed_url(version='v4', expiration=datetime.timedelta(minutes=self.minutes), method='GET',
                                        service_account_email=creds.service_account_email, access_token=creds.token)

    def put(self, data, mime):
        """-> (the signed URL, the object's name). The name is ours (a random token), never the member's file name or key."""
        name = PREFIX + secrets.token_hex(16)
        blob = self.bucket.blob(name)
        blob.upload_from_string(bytes(data), content_type=mime)
        return self.signer(blob), name

    def drop(self, name):
        """The object deleted (the make has ended). Never raises: a failed delete is logged by the object's name only, and the
        bucket's lifecycle rule takes it within a day."""
        if not NAME.fullmatch(str(name or '')):
            return False
        try:
            self.bucket.blob(name).delete()
            return True
        except Exception:   # noqa: BLE001 - the lifecycle rule is the floor
            LOG.warning('handoff %s not deleted now: the lifecycle rule deletes it within a day', name)
            return False


def from_environment():
    """Cloud Run's handoff (its lockers bucket, LARRYD_LOCKERS, with the cloud's own LARRYD_KEYS_DIR), or None on a laptop or in a test."""
    if os.environ.get('LARRYD_KEYS_DIR') and os.environ.get('LARRYD_LOCKERS'):
        return Handoff(os.environ['LARRYD_LOCKERS'])
    return None
