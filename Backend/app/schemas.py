"""
Pydantic schemas for request/response models.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models import StoreType, StoreStatus


# ---------- Request Schemas ----------
class StoreCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$")
    store_type: StoreType


# ---------- Response Schemas ----------
class StoreResponse(BaseModel):
    id: str
    name: str
    store_type: StoreType
    status: StoreStatus
    namespace: str
    store_url: Optional[str] = None
    admin_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StoreListResponse(BaseModel):
    stores: list[StoreResponse]
    total: int


class MessageResponse(BaseModel):
    message: str
    store_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    kubernetes_connected: bool
    version: str
