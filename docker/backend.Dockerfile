FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY backend backend
COPY attendance attendance
COPY camera camera
COPY face_engine face_engine
COPY migrations migrations
COPY scripts scripts
COPY alembic.ini .

EXPOSE 8000

CMD ["sh", "-c", "python -m scripts.bootstrap_db && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
