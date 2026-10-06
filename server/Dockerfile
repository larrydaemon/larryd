# THE LARRYD RUNTIME ON CLOUD RUN (the runtime design, 2026-10-06): the runtime only, run as its own non-root user.
# No instance, secret or venv is ever copied in (.dockerignore); the callers' keys are mounted by Cloud Run from Secret
# Manager at /keys, the instance is the container's own scratch space (the lockers and run records move to Cloud
# Storage and Firestore in the next step of the design).
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends bubblewrap && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 10001 larryd
WORKDIR /srv
COPY requirements.txt requirements-cloud.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-cloud.txt
COPY hanzo ./hanzo
RUN mkdir -p /srv/instance /srv/instance/secrets && chown -R larryd:larryd /srv/instance
USER larryd
ENV PYTHONUNBUFFERED=1 LARRYD_INSTANCE=/srv/instance LARRYD_HOST=0.0.0.0 LARRYD_KEYS_DIR=/keys LARRYD_NONCES=firestore HANZO_ENV=cloud.pf
CMD ["python", "hanzo/app/web/app.py"]
