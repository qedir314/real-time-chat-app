from pydantic import BaseModel, EmailStr, Field, field_validator

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=5)

    @field_validator('password')
    def validate_password_length(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be 72 bytes or less')
        return v

class UserInDB(User):
    hashed_password: str
