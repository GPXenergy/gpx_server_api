FROM python:3.12-slim-bookworm

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Django settings file
ENV DJANGO_SETTINGS_MODULE="gpx_server.settings"

# Django environment settings
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /gpx

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY --chown=appuser:appuser . .

# Create staticfiles directory with correct permissions
run mkdir -p /gpx/static && chown -R appuser:appuser /gpx/static

# Switch to non-root user
USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["sh", "./docker_entry.sh"]
