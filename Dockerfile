# Multi-stage Dockerfile for PitchSense Studio
# Stage 1: Build Frontend (Vite + React + Tailwind CSS v4)
FROM node:22-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend (FastAPI + uv)
FROM python:3.12-slim AS runner
WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install Python dependencies; exclude the local project itself until source files are copied.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source
COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose HTTP port for Azure Container Apps
EXPOSE 8000
ENV PORT=8000
ENV PSENSE_FAKE_MODEL=1

CMD ["/app/.venv/bin/uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
