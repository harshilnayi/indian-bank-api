# Indian Banks API

A REST + GraphQL API server for querying Indian bank branch data. Built with FastAPI and backed by SQLite.

The data comes from RBI's bank branch records (via [this dataset](https://github.com/Amanskywalker/indian_banks)) and covers ~127,000 branches across 170 banks.

---

## Quick Start

### Prerequisites
- Python 3.9+
- pip

### Setup

```bash
# clone and enter the project
git clone https://github.com/harshilnayi/indian-bank-api.git
cd indian-bank-api

# create a virtual env (recommended)
python -m venv venv
source venv/bin/activate   # on windows: venv\Scripts\activate

# install dependencies
pip install -r requirements.txt

# import bank data into the database
python scripts/import_data.py
```

### Run the Server

```bash
uvicorn app.main:app --reload
```

The server starts at `http://localhost:8000`. You'll find:

| URL | Description |
|-----|-------------|
| `http://localhost:8000/docs` | Interactive Swagger docs |
| `http://localhost:8000/gql` | GraphQL playground |
| `http://localhost:8000/api/banks` | REST - list all banks |

---

## API Endpoints

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/banks` | List all banks (paginated) |
| GET | `/api/banks/{id}` | Get a specific bank |
| GET | `/api/banks/{id}/branches` | List branches for a bank |
| GET | `/api/branches/{ifsc}` | Look up branch by IFSC code |
| GET | `/api/branches/search` | Search branches (by city, state, bank name) |

All list endpoints support `limit` and `offset` query params for pagination.

**Examples:**
```bash
# get first 5 banks
curl http://localhost:8000/api/banks?limit=5

# look up a branch
curl http://localhost:8000/api/branches/SBIN0000001

# search branches in Mumbai
curl "http://localhost:8000/api/branches/search?city=MUMBAI&limit=10"
```

### GraphQL

Available at `/gql`. Here's the query format:

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

You can also filter and paginate:

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

Other available queries: `banks`, `bank(id)`, `branch(ifsc)`.

---

## Running Tests

```bash
pytest tests/ -v -p no:asyncio
```

Tests cover:
- All REST endpoints (list, detail, search, pagination, 404 handling)
- GraphQL queries (the sample query format, filtering, lookups)

---

## Project Structure

```
indian-bank-api/
├── app/
│   ├── main.py           # FastAPI app setup
│   ├── database.py       # Database connection
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic response schemas
│   ├── routers/
│   │   └── banks.py      # REST endpoints
│   └── graphql/
│       └── schema.py     # GraphQL schema (Strawberry)
├── scripts/
│   └── import_data.py    # CSV to SQLite import
├── tests/
│   ├── test_rest.py      # REST API tests
│   └── test_graphql.py   # GraphQL tests
├── data/
│   └── bank_branches.csv # Source data
├── requirements.txt
└── README.md
```

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (via SQLAlchemy ORM)
- **GraphQL**: Strawberry GraphQL
- **Testing**: pytest + FastAPI TestClient

## Time Taken

About 2 days — spent time on design decisions, implementation, writing tests, and documentation.
