from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from models import User, UserWithAge, Feedback

app = FastAPI()

feedbacks = []

class Numbers(BaseModel):
    num1: float
    num2: float

user = User(name="Алина Гревцева", id=1)

@app.get("/")
async def root():
    return FileResponse("index.html", media_type="text/html; charset=utf-8")

@app.post("/calculate")
async def calculate(numbers: Numbers):
    return JSONResponse(
        content={"result": numbers.num1 + numbers.num2},
        media_type="application/json; charset=utf-8"
    )

@app.get("/users")
async def get_user():
    return JSONResponse(
        content={"name": user.name, "id": user.id},
        media_type="application/json; charset=utf-8"
    )

@app.post("/user")
async def check_user(user: UserWithAge):
    return JSONResponse(
        content={
            "name": user.name,
            "age": user.age,
            "is_adult": user.age >= 18
        },
        media_type="application/json; charset=utf-8"
    )

@app.post("/feedback")
async def add_feedback(fb: Feedback):
    feedbacks.append(fb)
    return JSONResponse(
        content={"message": f"Спасибо, {fb.name}! Ваш отзыв сохранён."},
        media_type="application/json; charset=utf-8"
    )

@app.get("/feedbacks")
async def get_feedbacks():
    return JSONResponse(
        content=[{"name": fb.name, "message": fb.message} for fb in feedbacks],
        media_type="application/json; charset=utf-8"
    )
