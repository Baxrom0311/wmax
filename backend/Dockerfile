# Multi-stage build: builder builds C extensions without leaving build-essential in final image.
# Non-root execution: runs under unprivileged user `wmax` (UID 10001).

FROM python:3.12-slim AS builder
WORKDIR /srv
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt       /tmp/req-core.txt
COPY backend/algo/requirements.txt  /tmp/req-algo.txt
COPY backend/auth/requirements.txt  /tmp/req-auth.txt
COPY notifier/requirements.txt      /tmp/req-notif.txt
RUN pip install --no-cache-dir --prefix=/install \
      -r /tmp/req-core.txt -r /tmp/req-algo.txt \
      -r /tmp/req-auth.txt -r /tmp/req-notif.txt

FROM python:3.12-slim
WORKDIR /srv
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/srv:/srv/backend:/srv/contracts

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 wmax

COPY --from=builder /install /usr/local
COPY contracts/ /srv/contracts/
COPY backend/   /srv/backend/
COPY notifier/  /srv/notifier/
COPY scripts/   /srv/scripts/

RUN mkdir -p /srv/notifier/data \
    && chmod +x /srv/backend/entrypoint.sh \
    && chown -R wmax:wmax /srv
USER wmax

EXPOSE 8000
ENTRYPOINT ["/srv/backend/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "/srv/backend"]
