# THE LARRYD RUNTIME ON CLOUD RUN (the runtime design, 2026-10-06): the runtime only, run as its own non-root user.
# No instance, secret or venv is ever copied in (.dockerignore); the callers' keys are mounted by Cloud Run from Secret
# Manager at /keys (one folder per slot, a file per mounted version), the runtime's own keys back to the slots at /out;
# the instance is the container's own scratch space only: the run records are Firestore's, the lockers the bucket's,
# a long run is its own Cloud Run job (the independent review, 2026-10-06).
# GATE 1 (the owner, 2026-10-06): the base moved from python:3.12-slim (Debian 13: 7 HIGH findings in perl, gcc-14,
# acl, attr and zlib with no fix published) to the slimmer Alpine one, upgraded at build; the image is accepted only
# when the registry's scan shows zero HIGH and zero CRITICAL.
FROM python:3.12-alpine
RUN apk upgrade --no-cache && apk add --no-cache bubblewrap \
 && adduser -D -u 10001 larryd
WORKDIR /srv
COPY requirements.txt requirements-cloud.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-cloud.txt
COPY runtime ./runtime
RUN mkdir -p /srv/instance /srv/instance/secrets && chown -R larryd:larryd /srv/instance
USER larryd
ENV PYTHONUNBUFFERED=1 LARRYD_INSTANCE=/srv/instance LARRYD_HOST=0.0.0.0 LARRYD_KEYS_DIR=/keys LARRYD_OUTBOUND_DIR=/out \
    LARRYD_NONCES=firestore LARRYD_RECORDS=firestore LARRYD_LOCKERS=larryd-runtime-lockers LARRYD_JOB=larryd-runtime-job \
    LARRYD_REGION=us-central1 LARRYD_ENV=cloud.pf
CMD ["python", "runtime/app/web/app.py"]
