# Slashit backend. Python 3.12 per decision AD-6 in the tech stack.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

# Dependencies first, so a source change does not reinstall them.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Never run as root. A container that does is one bug from being a host problem.
RUN useradd --create-home --uid 10001 slashit
USER slashit

EXPOSE 8000

# No secrets in this file and none baked into the image. FR-1 requires the
# credential to arrive from the environment at run time.
#
# The same image runs the job worker as a second container (epic 003, AD-9),
# with its command overridden to:
#
#   python -m procrastinate --app=app.core.jobs.procrastinate_app worker --concurrency=10
#
# `python -m` puts the working directory on the path, which the bare
# `procrastinate` script does not. Concurrency 10 fired 2,000 reminders due in
# one minute at a p95 of 28.5 s locally, against NFR-1's 60 s (003 dev log).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
