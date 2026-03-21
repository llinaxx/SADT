from fastapi import FastAPI, Response, HTTPException, Cookie, Header, Form
from typing import Optional
import uuid
import time
import os
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from models import UserCreate, CommonHeaders

app = FastAPI(title="SADT - Контрольная работа №2")

SECRET_KEY = os.environ.get("SECRET_KEY", "my-super-secret-key")
serializer = URLSafeTimedSerializer(SECRET_KEY)

users_db = {
    "alina_grevtseva": {"password": "alina123", "name": "Алина Гревцева", "email": "alina.grevtseva@mail.ru"}
}

sessions = {}
sessions_extended = {}

# 3.1
@app.post("/create_user")
async def create_user(user: UserCreate):
    return user

# 3.2
products = [
    {"product_id": 123, "name": "Smartphone", "category": "Electronics", "price": 599.99},
    {"product_id": 456, "name": "Phone Case", "category": "Accessories", "price": 19.99},
    {"product_id": 789, "name": "Iphone", "category": "Electronics", "price": 1299.99},
    {"product_id": 101, "name": "Headphones", "category": "Accessories", "price": 99.99},
    {"product_id": 202, "name": "Smartwatch", "category": "Electronics", "price": 299.99}
]

@app.get("/product/{product_id}")
async def get_product(product_id: int):
    for product in products:
        if product["product_id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")

@app.get("/products/search")
async def search_products(keyword: str, category: Optional[str] = None, limit: int = 10):
    result = [p for p in products if keyword.lower() in p["name"].lower()]
    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]
    return result[:limit]

# 5.1
@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...), response: Response = None):
    if username not in users_db or users_db[username]["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    session_token = str(uuid.uuid4())
    sessions[session_token] = {
        "username": username,
        "name": users_db[username]["name"],
        "email": users_db[username]["email"]
    }
    
    response.set_cookie(key="session_token", value=session_token, httponly=True, max_age=3600)
    return {"message": "Login successful"}

@app.get("/user")
async def get_user(session_token: Optional[str] = Cookie(None)):
    if not session_token or session_token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return sessions[session_token]

# 5.2
@app.post("/login/signed")
async def login_signed(username: str = Form(...), password: str = Form(...), response: Response = None):
    if username not in users_db or users_db[username]["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_id = str(uuid.uuid4())
    signed_token = serializer.dumps(user_id)
    
    response.set_cookie(key="session_token", value=signed_token, httponly=True, max_age=3600)
    
    sessions[user_id] = {
        "id": user_id,
        "username": username,
        "name": users_db[username]["name"],
        "email": users_db[username]["email"]
    }
    return {"message": "Login successful"}

@app.get("/profile")
async def get_profile(session_token: Optional[str] = Cookie(None)):
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        user_id = serializer.loads(session_token, max_age=3600)
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=401, detail="Invalid session")
    if user_id not in sessions:
        raise HTTPException(status_code=401, detail="Session expired")
    return sessions[user_id]

# 5.3
@app.post("/login/extended")
async def login_extended(username: str = Form(...), password: str = Form(...), response: Response = None):
    if username not in users_db or users_db[username]["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_id = str(uuid.uuid4())
    current_time = int(time.time())
    data_to_sign = f"{user_id}.{current_time}"
    signed_token = serializer.dumps(data_to_sign)
    
    response.set_cookie(key="session_token", value=signed_token, httponly=True, max_age=300)
    
    sessions_extended[user_id] = {
        "user_data": {
            "id": user_id,
            "username": username,
            "name": users_db[username]["name"],
            "email": users_db[username]["email"]
        },
        "last_activity": current_time
    }
    return {"message": "Login successful"}

@app.get("/profile/extended")
async def get_profile_extended(response: Response, session_token: Optional[str] = Cookie(None)):
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        signed_data = serializer.loads(session_token, max_age=300)
        parts = signed_data.split('.')
        if len(parts) != 2:
            raise BadSignature()
        user_id = parts[0]
        token_timestamp = int(parts[1])
    except (BadSignature, SignatureExpired, ValueError):
        raise HTTPException(status_code=401, detail="Invalid session")
    
    if user_id not in sessions_extended:
        raise HTTPException(status_code=401, detail="Session expired")
    
    current_time = int(time.time())
    last_activity = sessions_extended[user_id]["last_activity"]
    time_since_last = current_time - last_activity
    
    if time_since_last > 300:
        del sessions_extended[user_id]
        raise HTTPException(status_code=401, detail="Session expired")
    
    if 180 <= time_since_last < 300:
        new_timestamp = current_time
        sessions_extended[user_id]["last_activity"] = new_timestamp
        new_data_to_sign = f"{user_id}.{new_timestamp}"
        new_signed_token = serializer.dumps(new_data_to_sign)
        response.set_cookie(key="session_token", value=new_signed_token, httponly=True, max_age=300)
        return {"message": "Session extended", "user": sessions_extended[user_id]["user_data"]}
    
    return sessions_extended[user_id]["user_data"]

# 5.4
@app.get("/headers")
async def get_headers(user_agent: str = Header(...), accept_language: str = Header(...)):
    return {"User-Agent": user_agent, "Accept-Language": accept_language}

@app.get("/info")
async def get_info(
    response: Response,
    user_agent: str = Header(...),
    accept_language: str = Header(...)
):
    response.headers["X-Server-Time"] = datetime.now().isoformat()
    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": {
            "User-Agent": user_agent,
            "Accept-Language": accept_language
        }
    }
