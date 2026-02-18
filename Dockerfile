FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directory for SQLite persistence
RUN mkdir -p /app/data

EXPOSE 8001

ENV DEBUG=False
ENV SECRET_KEY=your-django-secret-key-here
ENV JWT_SECRET=your-super-secret-jwt-key-here-change-in-production
ENV LOG_LEVEL=INFO
ENV CORS_ALLOWED_ORIGINS=http://localhost:5000,http://127.0.0.1:5000,HTTP://0.0.0.0:5000
ENV ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
ENV DATABASE_PATH=/app/data/db.sqlite3

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8001"]
