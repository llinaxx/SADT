from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from passlib.context import CryptContext
import secrets
import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()

MODE = os.getenv("MODE", "DEV")
DOCS_USER = os.getenv("DOCS_USER", "admin")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD", "admin123")
SECRET_KEY = os.getenv("SECRET_KEY", "my-super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="SADT - Контрольная работа №3")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# База пользователей
users_db = {}

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Модели
class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# 6.5 - Регистрация с rate limit
@app.post("/register")
@limiter.limit("1/minute")
async def register(user: UserRegister, request=None):
    if user.username in users_db:
        raise HTTPException(status_code=409, detail="User already exists")
    
    hashed_password = get_password_hash(user.password)
    users_db[user.username] = {"username": user.username, "hashed_password": hashed_password}
    
    return {"message": "New user created"}

# 6.5 - Логин с rate limit
@app.post("/login")
@limiter.limit("5/minute")
async def login(user: UserLogin, request=None):
    if user.username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(user.password, users_db[user.username]["hashed_password"]):
        raise HTTPException(status_code=401, detail="Authorization failed")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# 6.5 - Защищенный ресурс
@app.get("/protected_resource")
async def protected_resource(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"message": f"Access granted for user {payload.get('sub')}"}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# 6.1 - Простая аутентификация
security = HTTPBasic()

def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = users_db.get(credentials.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"})
    if not secrets.compare_digest(credentials.username, user["username"]):
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"})
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"})
    return user

@app.get("/secret")
async def get_secret(user=Depends(authenticate_user)):
    return {"message": "You got my secret, welcome"}

# 6.3 - Защита документации
def protect_docs(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
    correct_username = secrets.compare_digest(credentials.username, DOCS_USER)
    correct_password = secrets.compare_digest(credentials.password, DOCS_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Incorrect credentials", headers={"WWW-Authenticate": "Basic"})
    return credentials.username

if MODE == "PROD":
    app.docs_url = None
    app.redoc_url = None
    app.openapi_url = None
else:
    from fastapi.openapi.docs import get_swagger_ui_html
    
    @app.get("/docs", include_in_schema=False)
    async def get_docs(_=Depends(protect_docs)):
        return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")
    
    @app.get("/openapi.json", include_in_schema=False)
    async def get_openapi(_=Depends(protect_docs)):
        return app.openapi()

@app.get("/")
async def root():
    return {"message": f"App running in {MODE} mode"}
from models import UserRole

# Расширенная база пользователей с ролями
users_with_roles = {
    "admin": {"password": "admin123", "role": UserRole.ADMIN},
    "user": {"password": "user123", "role": UserRole.USER},
    "guest": {"password": "guest123", "role": UserRole.GUEST}
}

# Функция проверки роли
def require_role(required_role: UserRole):
    def role_checker(credentials: HTTPBasicCredentials = Depends(security)):
        user = users_with_roles.get(credentials.username)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not secrets.compare_digest(credentials.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if user["role"] != required_role and user["role"] != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        return user
    return role_checker

# 7.1 - Эндпоинты с разными ролями
@app.get("/admin/resource")
async def admin_resource(user=Depends(require_role(UserRole.ADMIN))):
    return {"message": f"Admin access granted for {user['role']}"}

@app.get("/user/resource")
async def user_resource(user=Depends(require_role(UserRole.USER))):
    return {"message": f"User access granted for {user['role']}"}

@app.get("/guest/resource")
async def guest_resource(user=Depends(require_role(UserRole.GUEST))):
    return {"message": f"Guest access granted for {user['role']}"}

@app.post("/admin/create")
async def admin_create(user=Depends(require_role(UserRole.ADMIN))):
    return {"message": "Resource created by admin"}

@app.put("/user/update")
async def user_update(user=Depends(require_role(UserRole.USER))):
    return {"message": "Resource updated by user"}

@app.delete("/admin/delete")
async def admin_delete(user=Depends(require_role(UserRole.ADMIN))):
    return {"message": "Resource deleted by admin"}
from database import get_db_connection

# 8.1 - Регистрация в SQLite
class SQLiteUser(BaseModel):
    username: str
    password: str

@app.post("/db/register")
async def db_register(user: SQLiteUser):
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (user.username, user.password)
            )
            conn.commit()
        return {"message": "User registered successfully!"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
import sqlite3
