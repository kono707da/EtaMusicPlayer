FROM node:20-alpine AS frontend-builder

WORKDIR /build/frontend
COPY web/frontend/package.json web/frontend/package-lock.json ./
RUN npm ci
COPY web/frontend/ ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

COPY web/backend/ /app/web/backend/

COPY --from=frontend-builder /build/frontend/dist /app/web/frontend/dist

COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

RUN mkdir -p /app/web/backend/data /app/node /app/plugins /app/deps

EXPOSE 8000

VOLUME ["/app/web/backend/data", "/app/node", "/app/plugins", "/app/data", "/app/deps"]

ENV TZ=Asia/Shanghai

WORKDIR /app/web/backend

CMD ["/app/docker-entrypoint.sh"]
