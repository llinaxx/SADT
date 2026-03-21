from fastapi import FastAPI
from models import UserCreate

app = FastAPI(title="SADT - Контрольная работа №2")

# Задание 3.1
@app.post("/create_user")
async def create_user(user: UserCreate):
    return user

# Задание 3.2 - Данные о продуктах
products = [
    {"product_id": 123, "name": "Smartphone", "category": "Electronics", "price": 599.99},
    {"product_id": 456, "name": "Phone Case", "category": "Accessories", "price": 19.99},
    {"product_id": 789, "name": "Iphone", "category": "Electronics", "price": 1299.99},
    {"product_id": 101, "name": "Headphones", "category": "Accessories", "price": 99.99},
    {"product_id": 202, "name": "Smartwatch", "category": "Electronics", "price": 299.99}
]

# GET /product/{product_id}
@app.get("/product/{product_id}")
async def get_product(product_id: int):
    for product in products:
        if product["product_id"] == product_id:
            return product
    return {"error": "Product not found"}

# GET /products/search
@app.get("/products/search")
async def search_products(
    keyword: str,
    category: str = None,
    limit: int = 10
):
    result = [p for p in products if keyword.lower() in p["name"].lower()]
    
    # Фильтруем по категории, если указана
    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]
    
    return result[:limit]
from fastapi import Response, HTTPException, Cookie
from fastapi.responses import JSONResponse
from typing import Optional
import uuid
import json

# Задание 5.1 - Хранилище сессий (простое)
sessions = {}  # token -> user_info

users_db = {
    "user123": {"password": "alina123", "name": "Alina", "email": "alina@example.com"}
}

@app.post("/login")
async def login(username: str, password: str, response: Response):
    if username not in users_db or users_db[username]["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    session_token = str(uuid.uuid4())
    
    sessions[session_token] = {
        "username": username,
        "name": users_db[username]["name"],
        "email": users_db[username]["email"]
    }
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=3600  # 1 час
    )
    
    return {"message": "Login successful"}

@app.get("/user")
async def get_user(session_token: Optional[str] = Cookie(None)):
    if not session_token or session_token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return sessions[session_token]

@app.post("/login")
async def login(username: str, password: str, response: Response):
    if username not in users_db or users_db[username]["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    session_token = str(uuid.uuid4())
    sessions[session_token] = {
        "username": username,
        "name": users_db[username]["name"],
        "email": users_db[username]["email"]
    }
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=3600
    )
    return {"message": "Login successful"}
