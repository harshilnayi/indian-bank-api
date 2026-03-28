# Indian Banks API

This is a FastAPI service for querying Indian bank branch data from the RBI dataset published in the [`indian_banks`](https://github.com/Amanskywalker/indian_banks) repository.

The assignment only required one interface, but I chose to implement both:

- A REST API for common lookups
- A GraphQL API at `/gql` that supports the sample nested query from the assignment

The imported dataset contains about 127k branches across 170 banks.

## What Is Included

- GraphQL endpoint at `/gql`
- REST endpoints for banks, branches, and filtered branch search
- SQLite database with an import script for rebuilding from CSV
- Automated tests for both REST and GraphQL
- Deployment-ready config for Render plus a Docker setup
- A small health endpoint at `/health` for quick verification after deploys

## Quick Start

### Prerequisites

- Python 3.9+
- `pip`

### Setup

```bash
git clone https://github.com/harshilnayi/indian-bank-api.git
cd indian-bank-api

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
python scripts/import_data.py
```

### Run Locally

```bash
uvicorn app.main:app --reload
```

Once the server is running:

- Swagger docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- GraphQL playground: `http://localhost:8000/gql`
- Health check: `http://localhost:8000/health`

## REST API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/banks` | List banks with pagination |
| GET | `/api/banks/{id}` | Get one bank with branch count |
| GET | `/api/banks/{id}/branches` | List branches for a bank |
| GET | `/api/branches/{ifsc}` | Look up a branch by IFSC |
| GET | `/api/branches/search` | Search by city, state, branch name, or bank name |

List endpoints support `limit` and `offset`.

Example requests:

```bash
curl http://localhost:8000/api/banks?limit=5
curl http://localhost:8000/api/branches/SBIN0000001
curl "http://localhost:8000/api/branches/search?city=MUMBAI&limit=10"
```

## GraphQL API

The GraphQL endpoint is available at `/gql`.

This query matches the shape shown in the assignment:

```graphql
query {
  branches {
    edges {
      node {
        branch
        bank {
          name
        }
        ifsc
      }
    }
  }
}
```

Filtering and pagination are also supported:

```graphql
query {
  branches(city: "MUMBAI", first: 5) {
    edges {
      node {
        ifsc
        branch
        address
        bank {
          name
        }
      }
    }
    totalCount
  }
}
```

Other available queries:

- `banks`
- `bank(id)`
- `branch(ifsc)`

## Tests

Run the test suite with:

```bash
pytest tests/ -q -p no:asyncio
```

The tests cover:

- REST list and detail endpoints
- REST filtering and pagination
- 404 handling
- The exact GraphQL sample query from the assignment
- GraphQL pagination and lookup behavior

## Deployment

This repo is ready to deploy.

### Render

A [`render.yaml`](render.yaml) file is included. The build step installs dependencies and imports the CSV data into SQLite before the app starts.

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Docker

A [`Dockerfile`](Dockerfile) and [`.dockerignore`](.dockerignore) are included for container-based deployment.

Build and run locally with Docker:

```bash
docker build -t indian-bank-api .
docker run -p 8000:8000 indian-bank-api
```

## Project Structure

```text
indian-bank-api/
|-- app/
|   |-- main.py
|   |-- database.py
|   |-- models.py
|   |-- schemas.py
|   |-- graphql/
|   |   `-- schema.py
|   `-- routers/
|       `-- banks.py
|-- data/
|   `-- bank_branches.csv
|-- scripts/
|   `-- import_data.py
|-- tests/
|   |-- test_graphql.py
|   `-- test_rest.py
|-- requirements.txt
`-- README.md
```

## Tech Stack

- FastAPI
- Strawberry GraphQL
- SQLAlchemy
- SQLite
- pytest

## Time Taken

About 2 days. Most of the time went into designing the API shape, wiring both REST and GraphQL, importing the dataset cleanly, and writing tests.
