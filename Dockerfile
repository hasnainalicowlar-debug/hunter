# Dockerfile for Pakistan Food Business Intelligence & POS Platform
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure database directory exists and db is initialized if absent
RUN python -c "import os, sys; os.system('python database/db_manager.py') if not os.path.exists('database/food_intel.db') else print('Master 200k database detected.')"

EXPOSE 5000

ENV PORT=5000
ENV APP_ENV=production

# Production Gunicorn WSGI Server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120", "api.server:app"]
