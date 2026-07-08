FROM node:20-alpine AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt requests

COPY backend/ /app/backend/

COPY --from=frontend-builder /build/frontend/dist /app/frontend/dist

ENV ETA_HOST=0.0.0.0
ENV ETA_PORT=8000

RUN mkdir -p /app/backend/data /app/backend/data/uploads

EXPOSE 8000

VOLUME ["/app/backend/data"]

WORKDIR /app/backend

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
