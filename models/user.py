from pydantic import BaseModel, Field, field_validator
import re

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

    @field_validator('password')
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be 72 bytes or less')
        if not re.search(r"\d", v):
            raise ValueError('Password must contain at least one number')
        return v

class UserInDB(User):
    hashed_password: str
