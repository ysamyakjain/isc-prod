from pydantic import BaseModel
from typing import Optional
from pydantic import BaseModel, Field


# Model for user registration
class NewUserRegistration(BaseModel):
    username: str = Field(..., min_length=4)
    first_name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)
    email: str = Field(
        ..., min_length=5, pattern="^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    )
    phone: Optional[str] = None
    password: str = Field(..., min_length=8, max_length=16)

    class Config:
        extra = "forbid"


# Model for user login
class UserLogin(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

    class Config:
        extra = "forbid"


# Model for updating user details
class UpdateUser(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

    class Config:
        extra = "forbid"
