from pydantic import BaseModel
from typing import Optional, List

#events
class RegisterNewEvent(BaseModel):
    event_name: str
    event_image: Optional[str] = None
    discount_percent: int
    start_date: str
    end_date: str
    categories: str

class UpdateEvent(BaseModel):
    event_name: Optional[str] = None
    event_image: Optional[str] = None
    discount_percent: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    categories: Optional[str] = None
    class Config:
        extra = 'forbid'


