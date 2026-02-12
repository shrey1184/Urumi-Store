"""
SQLAlchemy models for the store provisioning platform.
"""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.sqlite import JSON

from app.database import Base


class StoreType(enum.StrEnum):
    WOOCOMMERCE = "woocommerce"


class StoreStatus(enum.StrEnum):
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
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    metadata_json = Column(JSON, nullable=True)  # Extra info (credentials, etc.)
