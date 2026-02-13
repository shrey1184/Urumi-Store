"""
SQLAlchemy models for the store provisioning platform.
"""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.database import Base


class StoreType(enum.StrEnum):
    WOOCOMMERCE = "woocommerce"
    MEDUSA = "medusa"


class StoreStatus(enum.StrEnum):
    PROVISIONING = "provisioning"
    READY = "ready"
    FAILED = "failed"
    DELETING = "deleting"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=True)
    oauth_provider = Column(String, nullable=False)  # google, github, etc.
    oauth_id = Column(String, nullable=False)  # unique ID from OAuth provider
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    last_login = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    stores = relationship("Store", back_populates="owner", cascade="all, delete-orphan")


class Store(Base):
    __tablename__ = "stores"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True, index=True)
    store_type = Column(SAEnum(StoreType), nullable=False)
    status = Column(SAEnum(StoreStatus), default=StoreStatus.PROVISIONING, nullable=False)
    namespace = Column(String, nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
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

    # Relationships
    owner = relationship("User", back_populates="stores")
