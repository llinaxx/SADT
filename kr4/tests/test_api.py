from fastapi.testclient import TestClient
from app import app
import pytest

client = TestClient(app)

def test_create_product():
    response = client.post("/products", json={
        "title": "Test Product",
        "price": 99.99,
        "count": 10
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Product"

def test_get_product_not_found():
    response = client.get("/products/99999")
    assert response.status_code == 404

def test_custom_exception_a():
    response = client.get("/test-exception-a?should_fail=true")
    assert response.status_code == 400

def test_custom_exception_b():
    response = client.get("/test-exception-b/0")
    assert response.status_code == 404

def test_register_valid_user():
    response = client.post("/register", json={
        "username": "testuser",
        "age": 25,
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200

def test_register_invalid_age():
    response = client.post("/register", json={
        "username": "testuser",
        "age": 16,
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 422
