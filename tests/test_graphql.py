"""
Tests for the GraphQL endpoint at /gql.

Makes sure the schema works with the exact query format
used in the documented example.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Bank, Branch


# separate test db for graphql tests
TEST_DB_URL = "sqlite:///./test_gql_data.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Create tables and seed data. Also patch SessionLocal for GraphQL resolvers."""
    Base.metadata.create_all(bind=test_engine)

    db = TestSession()
    bank = Bank(id=10, name="TEST BANK")
    db.add(bank)
    db.commit()

    branches = [
        Branch(ifsc="TEST0000001", bank_id=10, branch="BRANCH ONE",
               address="123 TEST STREET", city="TESTCITY",
               district="TESTDISTRICT", state="TESTSTATE"),
        Branch(ifsc="TEST0000002", bank_id=10, branch="BRANCH TWO",
               address="456 TEST AVENUE", city="OTHERCITY",
               district="OTHERDISTRICT", state="OTHERSTATE"),
    ]
    db.add_all(branches)
    db.commit()
    db.close()

    # patch the SessionLocal used by graphql resolvers
    import app.graphql.schema as gql_schema
    monkeypatch.setattr(gql_schema, "SessionLocal", TestSession)

    yield

    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)


class TestGraphQLQueries:

    def test_documented_sample_query(self):
        """
        This is the main nested query format documented in the README.
        It should keep working as the schema evolves.
        """
        query = """
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
        """
        resp = client.post("/gql", json={"query": query})
        assert resp.status_code == 200

        data = resp.json()
        assert "data" in data
        assert "branches" in data["data"]

        edges = data["data"]["branches"]["edges"]
        assert len(edges) > 0

        # check structure matches the documented nested query shape
        first_node = edges[0]["node"]
        assert "branch" in first_node
        assert "bank" in first_node
        assert "ifsc" in first_node
        assert "name" in first_node["bank"]

    def test_branches_with_pagination(self):
        query = """
        query {
            branches(first: 1) {
                edges {
                    node {
                        ifsc
                        branch
                    }
                }
                totalCount
            }
        }
        """
        resp = client.post("/gql", json={"query": query})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["branches"]["edges"]) == 1
        assert data["data"]["branches"]["totalCount"] == 2

    def test_branches_reject_negative_pagination(self):
        query = """
        query {
            branches(first: -1) {
                totalCount
            }
        }
        """
        resp = client.post("/gql", json={"query": query})
        assert resp.status_code == 200
        body = resp.json()
        assert "errors" in body
        assert "first must be greater than or equal to 0" in body["errors"][0]["message"]

    def test_banks_reject_negative_offset(self):
        query = """
        query {
            banks(offset: -1) {
                id
            }
        }
        """
        resp = client.post("/gql", json={"query": query})
        assert resp.status_code == 200
        body = resp.json()
        assert "errors" in body
        assert "offset must be greater than or equal to 0" in body["errors"][0]["message"]

    def test_branches_filter_by_city(self):
        query = """
        query {
            branches(city: "TESTCITY") {
                edges {
                    node {
                        ifsc
                        city
                    }
                }
                totalCount
            }
        }
        """
        resp = client.post("/gql", json={"query": query})
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["branches"]["totalCount"] == 1

    def test_single_branch_lookup(self):
        query = """
        query {
            branch(ifsc: "TEST0000001") {
                ifsc
                branch
                bank {
                    name
                }
            }
        }
        """
        resp = client.post("/gql", json={"query": query})
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["branch"]["ifsc"] == "TEST0000001"
        assert data["data"]["branch"]["bank"]["name"] == "TEST BANK"

    def test_branch_not_found(self):
        query = """
        query {
            branch(ifsc: "FAKE1234567") {
                ifsc
            }
        }
        """
        resp = client.post("/gql", json={"query": query})
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["branch"] is None

    def test_list_banks(self):
        query = """
        query {
            banks {
                id
                name
            }
        }
        """
        resp = client.post("/gql", json={"query": query})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["banks"]) == 1
        assert data["data"]["banks"][0]["name"] == "TEST BANK"

    def test_single_bank(self):
        query = """
        query {
            bank(id: 10) {
                id
                name
            }
        }
        """
        resp = client.post("/gql", json={"query": query})
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["bank"]["name"] == "TEST BANK"
