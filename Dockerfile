# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl gzip sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# Stage 2: Runtime image
FROM python:3.11-slim as runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl gzip sqlite3 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV PORT=8000
ENV DB_PATH=/app/data/fanqie.db
ENV DOWNLOAD_DIR=/app/data/downloads
ENV PROJECTS_DIR=/app/data/projects
ENV LOG_DIR=/app/data/logs

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY app ./app
COPY novel_creator ./novel_creator
COPY scripts ./scripts

RUN mkdir -p /app/data/logs /app/data/downloads /app/data/projects && \
    chown -R root:root /app/data && \
    chmod -R 755 /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
