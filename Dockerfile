# web
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build && npm run build:css

# 後端
FROM python:3.12-alpine
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN apk add --no-cache git

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .

COPY --from=frontend-builder /app/frontend/static/js ./frontend/static/js
COPY --from=frontend-builder /app/frontend/static/css/output.css ./frontend/static/css/output.css

EXPOSE 8000

CMD ["uv", "run", "main.py"]
