import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, get_db

# Real Postgres, but a SEPARATE database from dev/prod -- tests call
# create_all/drop_all around every test, which would destroy real data
# if this pointed at the same db as .env's database_url.
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/databoard_test"

engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def auth_headers(client):
    client.post("/auth/register", json={"email": "tester@example.com", "password": "password123"})
    resp = client.post("/auth/login", json={"email": "tester@example.com", "password": "password123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}