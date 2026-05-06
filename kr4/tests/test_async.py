import pytest
from httpx import AsyncClient, ASGITransport
from faker import Faker
from app import app

fake = Faker()

# Фикстура для очистки состояния
@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

# Тесты для задания 9.1 - Products
@pytest.mark.asyncio
async def test_create_product(client):
    product_data = {
        "title": fake.word(),
        "price": fake.random_number(digits=2),
        "count": fake.random_int(min=1, max=100)
    }
    response = await client.post("/products", json=product_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == product_data["title"]
    assert data["price"] == product_data["price"]
    assert data["count"] == product_data["count"]
    assert "id" in data

@pytest.mark.asyncio
async def test_get_product_not_found(client):
    response = await client.get("/products/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"

# Тесты для задания 10.1 - Пользовательские исключения
@pytest.mark.asyncio
async def test_custom_exception_a(client):
    response = await client.get("/test-exception-a?should_fail=true")
    assert response.status_code == 400
    assert "custom exception A" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_custom_exception_b(client):
    response = await client.get("/test-exception-b/0")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

# Тесты для задания 10.2 - Валидация
@pytest.mark.asyncio
async def test_register_valid_user(client):
    user_data = {
        "username": fake.user_name(),
        "age": 25,
        "email": fake.email(),
        "password": "password123",
        "phone": fake.phone_number()
    }
    response = await client.post("/register", json=user_data)
    assert response.status_code == 200
    assert response.json()["message"] == f"User {user_data['username']} registered successfully"

@pytest.mark.asyncio
async def test_register_invalid_age(client):
    user_data = {
        "username": fake.user_name(),
        "age": 16,  # меньше 18
        "email": fake.email(),
        "password": "password123"
    }
    response = await client.post("/register", json=user_data)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_register_invalid_email(client):
    user_data = {
        "username": fake.user_name(),
        "age": 25,
        "email": "invalid-email",
        "password": "password123"
    }
    response = await client.post("/register", json=user_data)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_register_short_password(client):
    user_data = {
        "username": fake.user_name(),
        "age": 25,
        "email": fake.email(),
        "password": "123"  # слишком короткий
    }
    response = await client.post("/register", json=user_data)
    assert response.status_code == 422
