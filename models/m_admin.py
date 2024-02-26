from typing import Optional
from pydantic import BaseModel

class UserLogin(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

    class Config:
        extra = "forbid"

class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str 
    country: str

class NewAdminRegistration(BaseModel):
    email: str
    username: str
    password: str
    first_name: str 
    last_name: str 
    gender: str
    profile_picture: Optional[str] 
    phone_number: str 
    address: Address

    class Config:
        extra = 'forbid'
        
