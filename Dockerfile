FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FASTF1_CACHE_DIR=/tmp/fastf1-cache
ENV PORT=7860

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend

WORKDIR /app/backend

EXPOSE 7860

CMD ["sh", "-c", "mkdir -p \"$FASTF1_CACHE_DIR\" && uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}"]
