FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.14-slim

WORKDIR /app
COPY requirements-web.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY --from=frontend-build /frontend/dist ./frontend/dist

ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers --forwarded-allow-ips=*"]