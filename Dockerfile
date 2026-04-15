# Use a slim Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies for MySQL driver and Gunicorn
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app
COPY . .

# Expose Flask port
EXPOSE 8000


CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers=4", "--threads=2", "--timeout", "120", "app:app"]
