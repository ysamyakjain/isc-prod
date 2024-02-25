from pydantic import BaseModel
from typing import Optional

class NewBeaconRegistration(BaseModel):
    mac_id: str
    device_id: str
    battery: int
    status: str

class BeaconUpdate(BaseModel):
    mac_id: Optional[str] = None
    device_id: Optional[str] = None
    battery: Optional[int] = None
    status: Optional[str] = None
    class Config:
        extra = 'forbid'