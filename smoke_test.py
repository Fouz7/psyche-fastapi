import os
import pathlib

# Use isolated test database to avoid schema conflicts
TEST_DB = pathlib.Path("app_test.db")
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

from fastapi.testclient import TestClient
from main import app

with TestClient(app) as client:
    # Register new user
    r = client.post("/auth/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret123"
    })
    print("register status:", r.status_code)
    print("register body:", r.json())

    r2 = client.post("/auth/register", json={
        "username": "alice",
        "email": "ALICE@EXAMPLE.COM",
        "password": "secret123"
    })
    print("dup register status:", r2.status_code)

    l1 = client.post("/auth/login", json={
        "username": "alice",
        "password": "secret123"
    })
    print("login-username status:", l1.status_code)
    print("login-username body:", l1.json())

    l2 = client.post("/auth/login", json={
        "username": "ALICE@example.com",
        "password": "secret123"
    })
    print("login-email status:", l2.status_code)
    print("login-email body:", l2.json())

    nf = client.post("/auth/login", json={
        "username": "doesnotexist",
        "password": "whatever"
    })
    print("login-not-found status:", nf.status_code)
    print("login-not-found body:", nf.json())

    wp = client.post("/auth/login", json={
        "username": "alice",
        "password": "wrongpass"
    })
    print("login-wrongpass status:", wp.status_code)
    print("login-wrongpass body:", wp.json())

    p = client.post("/mental/predict", json={
        "userId": 1,
        "language": "en",
        "appetite": 3,
        "interest": 4,
        "fatigue": 2,
        "worthlessness": 4,
        "concentration": 3,
        "agitation": 2,
        "suicidalIdeation": 6,
        "sleepDisturbance": 3,
        "aggression": 2,
        "panicAttacks": 5,
        "hopelessness": 3,
        "restlessness": 4
    })
    print("predict status:", p.status_code)
    print("predict body:", p.json())
