from typing import List, Optional
from pydantic import BaseModel

#shops models   
class Coordinates(BaseModel):
    lat: float
    long: float

class Location(BaseModel):
    city: str
    state: str
    country: str
    zipcode: str
    coordinates: Coordinates
 
class NewShopRegistration(BaseModel):
    store_category: str
    store_types: str
    location: Location
    contact: str
    floor_number: int
    shop_image: str
    store_name: str
    store_number: int
    tags: List[str]
    website: str
    description: str


class UpdateLocation(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zipcode: Optional[str] = None
    coordinates: Optional[Coordinates] = None
    class Config:
        extra = 'forbid'

class UpdateShopDetails(BaseModel):
    store_category: Optional[str] = None
    store_types: Optional[str] = None
    location: Optional[UpdateLocation] = None
    contact: Optional[str] = None
    floor_number: Optional[int] = None
    store_image: Optional[str] = None
    store_name: Optional[str] = None
    store_number: Optional[int] = None
    tags: Optional[List[str]] = None
    website: Optional[str] = None
    description: Optional[str] = None
    class Config:
        extra = 'forbid'


