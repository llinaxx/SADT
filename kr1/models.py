from pydantic import BaseModel, Field, field_validator
import re

class User(BaseModel):
    name: str
    id: int

class UserWithAge(BaseModel):
    name: str
    age: int

class Feedback(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    message: str = Field(..., min_length=10, max_length=500)
    
    @field_validator("message")
    def check_bad_words(cls, v):
        bad_words = ["крингк", "рофл", "вайб"]
        pattern = re.compile("|".join(bad_words), re.IGNORECASE)
        if pattern.search(v):
            raise ValueError("Использование недопустимых слов")
        return v
