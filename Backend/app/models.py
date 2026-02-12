"""
SQLAlchemy models for the store provisioning platform.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, Text
from sqlalchemy.dialects.sqlite import JSON
from app.database import Base
import enum


class StoreType(str, enum.Enum):
    WOOCOMMERCE = "woocommerce"
    MEDUSAJS = "medusajs"


class StoreStatus(str, enum.Enum):
    PROVISIONING = "provisioning"
    READY = "ready"
    FAILED = "failed"
    DELETING = "deleting"


class Store(Base):
    __tablename__ = "stores"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True, index=True)
    store_type = Column(SAEnum(StoreType), nullable=False)
    status = Column(SAEnum(StoreStatus), default=StoreStatus.PROVISIONING, nullable=False)
    namespace = Column(String, nullable=False, unique=True)
    store_url = Column(String, nullable=True)
    admin_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    metadata_json = Column(JSON, nullable=True)  # Extra info (credentials, etc.)
