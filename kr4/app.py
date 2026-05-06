from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db, engine
import models

app = FastAPI(title="SADT - Контрольная работа №4")

# Создаем таблицы
models.Base.metadata.create_all(bind=engine)

# Pydantic модели
class ProductCreate(BaseModel):
    title: str
    price: float
    count: int

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[float] = None
    count: Optional[int] = None
    description: Optional[str] = None

class ProductResponse(ProductCreate):
    id: int
    description: Optional[str] = None

# 9.1 - CRUD операции
@app.post("/products", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = models.Product(title=product.title, price=product.price, count=product.count, description="")
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
from fastapi import Request, status
from fastapi.responses import JSONResponse

# 10.1 - Пользовательские исключения
class CustomExceptionA(Exception):
    def __init__(self, message: str = "Custom Exception A occurred"):
        self.message = message
        self.status_code = 400

class CustomExceptionB(Exception):
    def __init__(self, message: str = "Resource not found"):
        self.message = message
        self.status_code = 404

# 10.1 - Модели ответов ошибок
class ErrorResponse(BaseModel):
    detail: str
    status_code: int

# 10.1 - Обработчики исключений
@app.exception_handler(CustomExceptionA)
async def custom_exception_a_handler(request: Request, exc: CustomExceptionA):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "status_code": exc.status_code}
    )

@app.exception_handler(CustomExceptionB)
async def custom_exception_b_handler(request: Request, exc: CustomExceptionB):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "status_code": exc.status_code}
    )

# 10.1 - Эндпоинты, вызывающие исключения
@app.get("/test-exception-a")
def test_exception_a(should_fail: bool = True):
    if should_fail:
        raise CustomExceptionA("This is a custom exception A")
    return {"message": "Success"}

@app.get("/test-exception-b/{item_id}")
def test_exception_b(item_id: int):
    if item_id == 0:
        raise CustomExceptionB(f"Item with id {item_id} not found")
    return {"message": f"Item {item_id} found"}
from pydantic import BaseModel, conint, constr, EmailStr, Field
from typing import Optional

# 10.2 - Модель пользователя с валидацией
class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    age: conint(gt=18)  # больше 18
    email: EmailStr
    password: constr(min_length=8, max_length=16)
    phone: Optional[str] = 'Unknown'

# 10.2 - Обработчик ошибок валидации
@app.exception_handler(Exception)
async def validation_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "status_code": 422}
    )

# 10.2 - Эндпоинт регистрации
@app.post("/register")
def register(user: User):
    return {"message": f"User {user.username} registered successfully", "user": user.dict()}
