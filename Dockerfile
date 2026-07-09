FROM node:20-alpine AS frontend-builder

WORKDIR /build/frontend
COPY web/frontend/package.json web/frontend/package-lock.json ./
RUN npm ci
COPY web/frontend/ ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY web/backend/requirements.txt /app/web/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/web/backend/requirements.txt

COPY node/requirements.txt /app/node/requirements.txt
RUN pip install --no-cache-dir -r /app/node/requirements.txt

COPY plugins/asmr_one/requirements.txt /app/plugins/asmr_one/requirements.txt
RUN pip install --no-cache-dir -r /app/plugins/asmr_one/requirements.txt

COPY plugins/bili_audio/requirements.txt /app/plugins/bili_audio/requirements.txt
RUN pip install --no-cache-dir -r /app/plugins/bili_audio/requirements.txt

COPY plugins/shared/requirements.txt /app/plugins/shared/requirements.txt
RUN pip install --no-cache-dir -r /app/plugins/shared/requirements.txt

COPY web/backend/ /app/web/backend/
COPY node/ /app/node/
COPY plugins/ /app/plugins/

COPY --from=frontend-builder /build/frontend/dist /app/web/frontend/dist

RUN mkdir -p /app/web/backend/data /app/node/data /app/plugins/asmr_one/data /app/plugins/bili_audio/data

EXPOSE 8000

VOLUME ["/app/web/backend/data", "/app/node/data"]

ENV TZ=Asia/Shanghai

WORKDIR /app/web/backend

CMD ["python", "-m", "uvicorn", "eta_web.main:app", "--host", "0.0.0.0", "--port", "8000"]
