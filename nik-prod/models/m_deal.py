from pydantic import BaseModel
from typing import Optional, List

#deals
class RegisterNewDeal(BaseModel):
    deal_name: str
    deal_image: Optional[str] = None
    discount_percent: int
    start_date: str
    end_date: str
    categories: str

class UpdateDeal(BaseModel):
    deal_name: Optional[str] = None
    deal_image: Optional[str] = None
    discount_percent: Optional[int] = None
    is_active: Optional[bool] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    categories: Optional[str] = None
    class Config:
        extra = 'forbid'


