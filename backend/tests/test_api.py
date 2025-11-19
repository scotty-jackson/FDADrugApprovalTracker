"""
Basic API tests for FDA Drug Approval Tracker
Run with: pytest tests/
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.main import app
from app.database import get_db
from app.models import Base

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test database
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_read_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "FDA Drug Approval Tracker API"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_get_drugs():
    """Test drugs endpoint"""
    response = client.get("/api/drugs")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


def test_get_approvals():
    """Test approvals endpoint"""
    response = client.get("/api/approvals")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_get_events():
    """Test events endpoint"""
    response = client.get("/api/events")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_get_upcoming_events():
    """Test upcoming events endpoint"""
    response = client.get("/api/events/upcoming")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_get_summary():
    """Test summary statistics endpoint"""
    response = client.get("/api/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_drugs" in data
    assert "total_approvals" in data
    assert "total_upcoming_events" in data


def test_get_sponsors():
    """Test sponsors endpoint"""
    response = client.get("/api/summary/sponsors")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_pagination():
    """Test pagination parameters"""
    response = client.get("/api/drugs?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 10


def test_filters():
    """Test filter parameters"""
    response = client.get("/api/approvals?fda_center=CDER")
    assert response.status_code == 200

    response = client.get("/api/approvals?application_type=NDA")
    assert response.status_code == 200


def test_search():
    """Test search functionality"""
    response = client.get("/api/drugs?search=test")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


# Cleanup
def teardown_module(module):
    """Clean up test database"""
    import os
    if os.path.exists("./test.db"):
        os.remove("./test.db")
