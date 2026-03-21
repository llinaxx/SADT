from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re

# 3.1
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: Optional[int] = Field(None, ge=0, le=150)
    is_subscribed: Optional[bool] = False

# 5.2
class UserProfile(BaseModel):
    id: str
    username: str
    name: str
    email: str

# 5.4
class CommonHeaders(BaseModel):
    user_agent: str = Field(..., alias="User-Agent")
    accept_language: str = Field(..., alias="Accept-Language")
    
    @field_validator("accept_language")
    @classmethod
    def validate_accept_language(cls, v):
        pattern = r'^[a-z]{2}(-[A-Z]{2})?(;q=[0-9]\.[0-9])?(,[a-z]{2}(-[A-Z]{2})?(;q=[0-9]\.[0-9])?)*$'
        if not re.match(pattern, v) and v != "*":
            if not re.match(r'^[a-z]{2}(-[A-Z]{2})?$', v):
                raise ValueError(f"Invalid Accept-Language format: {v}")
        return v
    
    class Config:
        populate_by_name = True
