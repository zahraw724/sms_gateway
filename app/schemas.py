from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ProviderCreate(BaseModel):
    name: str
    adapter_type: str
    config: Dict[str, Any]
    sender_number: str
    priority: Optional[int] = 1

class SendSMSRequest(BaseModel):
    recipient: str = Field(..., pattern=r"^09\d{9}$")
    body: str
    message_type: Optional[str] = "info"

class OTPRequest(BaseModel):
    phone: str = Field(..., pattern=r"^09\d{9}$")

class OTPVerifyRequest(BaseModel):
    phone: str = Field(..., pattern=r"^09\d{9}$")
    code: str