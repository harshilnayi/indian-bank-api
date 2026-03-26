"""
Tests for the REST API endpoints.

Uses FastAPI's TestClient which doesn't need a running server.
We set up a small test database with known data so tests are predictable.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Bank, Branch


# use in-memory sqlite for tests - fast and disposable
TEST_DB_URL = "sqlite:///./test_bank_data.db"
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
def setup_test_db():
    """Create tables and seed test data before each test."""
    Base.metadata.create_all(bind=test_engine)

    db = TestSession()
    # seed some test data
    bank1 = Bank(id=1, name="STATE BANK OF INDIA")
    bank2 = Bank(id=2, name="ICICI BANK LIMITED")
    db.add_all([bank1, bank2])
    db.commit()

    branches = [
        Branch(ifsc="SBIN0000001", bank_id=1, branch="MAIN BRANCH",
               address="11 PARLIAMENT STREET, NEW DELHI", city="NEW DELHI",
               district="NEW DELHI", state="DELHI"),
        Branch(ifsc="SBIN0000002", bank_id=1, branch="MUMBAI MAIN",
               address="MUMBAI MAIN BRANCH, FORT", city="MUMBAI",
               district="MUMBAI", state="MAHARASHTRA"),
        Branch(ifsc="ICIC0000001", bank_id=2, branch="CHENNAI",
               address="100 ANNA SALAI, CHENNAI", city="CHENNAI",
               district="CHENNAI", state="TAMIL NADU"),
    ]
    db.add_all(branches)
    db.commit()
    db.close()

    yield

    # cleanup after test
    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)


# --- Bank endpoint tests ---

class TestBankEndpoints:

    def test_list_banks(self):
        resp = client.get("/api/banks")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["data"]) == 2

    def test_list_banks_pagination(self):
        resp = client.get("/api/banks?limit=1&offset=0")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 1
        assert body["total"] == 2

    def test_get_bank_by_id(self):
        resp = client.get("/api/banks/1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "STATE BANK OF INDIA"
        assert body["branch_count"] == 2

    def test_get_bank_not_found(self):
        resp = client.get("/api/banks/999")
        assert resp.status_code == 404

    def test_get_bank_branches(self):
        resp = client.get("/api/banks/1/branches")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        # should all belong to SBI
        for branch in body["data"]:
            assert branch["bank_name"] == "STATE BANK OF INDIA"


# --- Branch endpoint tests ---

class TestBranchEndpoints:

    def test_get_branch_by_ifsc(self):
        resp = client.get("/api/branches/SBIN0000001")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ifsc"] == "SBIN0000001"
        assert body["branch"] == "MAIN BRANCH"
        assert body["bank_name"] == "STATE BANK OF INDIA"

    def test_get_branch_case_insensitive(self):
        """IFSC lookup should work regardless of case."""
        resp = client.get("/api/branches/sbin0000001")
        assert resp.status_code == 200

    def test_get_branch_not_found(self):
        resp = client.get("/api/branches/FAKE1234567")
        assert resp.status_code == 404

    def test_search_by_city(self):
        resp = client.get("/api/branches/search?city=MUMBAI")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        for branch in body["data"]:
            assert "MUMBAI" in branch["city"].upper()

    def test_search_by_state(self):
        resp = client.get("/api/branches/search?state=DELHI")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1

    def test_search_by_bank_name(self):
        resp = client.get("/api/branches/search?bank_name=ICICI")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["data"][0]["bank_name"] == "ICICI BANK LIMITED"

    def test_search_no_results(self):
        resp = client.get("/api/branches/search?city=NONEXISTENTCITY")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["data"] == []


class TestRootEndpoint:

    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert "endpoints" in body
        assert body["endpoints"]["graphql"] == "/gql"
