# Customer Data Pipeline

A 3-service Docker pipeline: Flask mock server → FastAPI ingestion → PostgreSQL storage.

## Architecture

```
Flask Mock Server (port 5000)
        │
        │  HTTP (paginated JSON)
        ▼
FastAPI Pipeline Service (port 8000)
        │
        │  SQLAlchemy upsert
        ▼
PostgreSQL (port 5432)
```

## Project Structure

```
project-root/
├── docker-compose.yml
├── README.md
├── mock-server/
│   ├── app.py
│   ├── data/customers.json
│   ├── Dockerfile
│   └── requirements.txt
└── pipeline-service/
    ├── main.py
    ├── database.py
    ├── models/
    │   ├── __init__.py
    │   └── customer.py
    ├── services/
    │   ├── __init__.py
    │   └── ingestion.py
    ├── Dockerfile
    └── requirements.txt
```

## Prerequisites

- Docker Desktop (running)
- Docker Compose v2+

## Quick Start

```bash
# 1. Start all services
docker-compose up -d

# 2. Verify all containers are healthy
docker-compose ps

# 3. Test Flask mock server health
curl http://localhost:5000/api/health

# 4. Get paginated customers from Flask
curl "http://localhost:5000/api/customers?page=1&limit=5"

# 5. Get single customer from Flask
curl http://localhost:5000/api/customers/CUST001

# 6. Trigger ingestion into PostgreSQL
curl -X POST http://localhost:8000/api/ingest

# 7. Get customers from PostgreSQL (via FastAPI)
curl "http://localhost:8000/api/customers?page=1&limit=5"

# 8. Get single customer from PostgreSQL
curl http://localhost:8000/api/customers/CUST001
```

## API Reference

### Flask Mock Server — `http://localhost:5000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/customers?page=1&limit=10` | Paginated customer list |
| GET | `/api/customers/{id}` | Single customer by ID |

**Paginated response format:**
```json
{
  "data": [...],
  "total": 22,
  "page": 1,
  "limit": 10
}
```

### FastAPI Pipeline — `http://localhost:8000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/ingest` | Fetch from Flask & upsert to PostgreSQL |
| GET | `/api/customers?page=1&limit=10` | Paginated results from DB |
| GET | `/api/customers/{id}` | Single customer from DB |

**Ingest response:**
```json
{
  "status": "success",
  "records_processed": 22
}
```

Interactive API docs available at: `http://localhost:8000/docs`

## Database Schema

```sql
CREATE TABLE customers (
    customer_id    VARCHAR(50)     PRIMARY KEY,
    first_name     VARCHAR(100)    NOT NULL,
    last_name      VARCHAR(100)    NOT NULL,
    email          VARCHAR(255)    NOT NULL,
    phone          VARCHAR(20),
    address        TEXT,
    date_of_birth  DATE,
    account_balance DECIMAL(15,2),
    created_at     TIMESTAMP
);
```

## Stopping Services

```bash
docker-compose down          # Stop containers
docker-compose down -v       # Stop and remove volumes (clears DB)
```

## Logs

```bash
docker-compose logs -f mock-server
docker-compose logs -f pipeline-service
docker-compose logs -f postgres
```
