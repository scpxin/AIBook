FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY novel_creator ./novel_creator

ENV PORT=8000
ENV DATABASE_PATH=/app/data/fanqie.db
ENV DOWNLOAD_DIR=/app/data/downloads
ENV PROJECTS_DIR=/app/data/projects
ENV LOG_DIR=/app/data/logs

RUN mkdir -p /app/data/logs /app/data/downloads /app/data/projects

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
