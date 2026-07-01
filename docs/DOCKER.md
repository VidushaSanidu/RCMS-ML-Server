# ML Server Docker (Development)

This guide explains how to run the Django ML Server using Docker in the development environment.

This setup uses:

* [`Dockerfile`](./Dockerfile)
* [`docker-compose.yml`](./docker-compose.yml)

The ML server will run on port **8001**.

---

## Prerequisites

Make sure you have installed:

* Docker
* Docker Compose

Verify installation:

```bash
docker --version
docker compose version
```

---

## Environment Variables Setup

```text
ML_Server/
├── Dockerfile
├── docker-compose.yml
├── .env
```

Example [`.env`](./.env.example) file:

```env
DEBUG=False

DJANGO_SECRET_KEY=your-django-secret-key-here

JWT_SECRET=your-super-secret-jwt-key-here-change-in-production

LOG_LEVEL=INFO

CORS_ALLOWED_ORIGINS=http://localhost:5000,http://127.0.0.1:5000

ALLOWED_HOSTS=localhost,127.0.0.1
    
DB_ENGINE=none
```

Refer to [`ENV.md`](./ENV.md) for full environment variable details.

---

## Build and Start the ML Server

Run from the project root:

```bash
docker compose -f docker-compose.yml up --build
```

This will:

* Build the Docker image using [`Dockerfile`](./Dockerfile)
* Start the ML server container
* Expose the server at:

```http
http://localhost:8001
```

---

## Run in Background Mode

```bash
docker compose -f docker-compose.yml up -d --build
```

---

## Stop the Server

```bash
docker compose -f docker-compose.yml down
```

---

## Rebuild After Code Changes

```bash
docker compose -f docker-compose.yml up --build
```

---

## Persistent Data (Optional)

SQLite database (if used) is stored in Docker volume:

```docker
renal_ml_data
```

Mapped to container path:

```docker
/app/data
```

This ensures data persistence between container restarts.

> Note: Database is optional and not required for ML inference.

---

## Verify Server

Open browser:

```http
http://localhost:8001
```

or test with curl:

```bash
curl http://localhost:8001
```

---
