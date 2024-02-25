from pydantic import BaseModel
from typing import Optional


class NewGatewayRegistration(BaseModel):
    longitude: float
    latitude: float
    altitude: str
    gw_name: str
    gw_ip_address: str
    gw_model: str
    gw_firmware: str
    gw_serial: str
    gw_location: str
    vendor_code: str
    
class GatewayUpdate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[str] = None
    gw_name: Optional[str] = None
    gw_ip_address: Optional[str] = None
    gw_model: Optional[str] = None
    gw_firmware: Optional[str] = None
    gw_serial: Optional[str] = None
    gw_location: Optional[str] = None
    vendor_code: Optional[str] = None
    class Config:
        extra = 'forbid'