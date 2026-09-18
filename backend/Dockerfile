# MUZLATILGAN (Task 0). Agentlar bu faylga tegmaydi.
# Bitta image — ikki jarayon: `api` (uvicorn) va `notifier` (scheduler+telegram).
# Shuning uchun notifier ham bir xil SQLAlchemy modellarni import qiladi: drift yo'q.
FROM python:3.12-slim

WORKDIR /srv
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/srv:/srv/backend:/srv/contracts

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl && rm -rf /var/lib/apt/lists/*

# Uchta alohida requirements — A1/A2/A6 bir faylda urishmasligi uchun.
COPY backend/requirements.txt       /tmp/req-core.txt
COPY backend/algo/requirements.txt  /tmp/req-algo.txt
COPY backend/auth/requirements.txt  /tmp/req-auth.txt
COPY notifier/requirements.txt      /tmp/req-notif.txt
RUN pip install --no-cache-dir \
      -r /tmp/req-core.txt -r /tmp/req-algo.txt \
      -r /tmp/req-auth.txt -r /tmp/req-notif.txt

COPY contracts/ /srv/contracts/
COPY backend/   /srv/backend/
COPY notifier/  /srv/notifier/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "/srv/backend"]
