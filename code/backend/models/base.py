"""
Base model classes with common functionality
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BaseModel(Base):
    """
    Base model class with common fields and functionality
    """

    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    @declared_attr
    def __tablename__(cls: Any) -> Any:
        """Generate table name from class name"""
        return cls.__name__.lower() + "s"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model instance from dictionary"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"


class TimestampMixin:
    """
    Mixin for adding timestamp fields
    """

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True,
    )


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality
    """

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True, index=True)

    def soft_delete(self) -> None:
        """Mark record as deleted"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore soft deleted record"""
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """
    Mixin for audit trail functionality
    """

    created_by = Column(UUID(as_uuid=True), nullable=True, index=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True, index=True)
    audit_metadata = Column(JSON, nullable=True)

    def set_audit_info(
        self, user_id: uuid.UUID, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set audit information"""
        if not self.created_by:
            self.created_by = user_id
        self.updated_by = user_id
        if metadata:
            self.audit_metadata = metadata


class EncryptedMixin:
    """
    Mixin for encrypted field support
    """

    encryption_key_id = Column(String(255), nullable=True)
    is_encrypted = Column(Boolean, default=False, nullable=False)

    def mark_encrypted(self, key_id: str) -> None:
        """Mark field as encrypted with key ID"""
        self.is_encrypted = True
        self.encryption_key_id = key_id


class VersionMixin:
    """
    Mixin for optimistic locking with version control
    """

    version = Column(Integer, default=1, nullable=False)

    def increment_version(self) -> None:
        """Increment version for optimistic locking"""
        self.version += 1


class MetadataMixin:
    """
    Mixin for storing additional metadata
    """

    extra_metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata key-value pair"""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key"""
        if self.metadata is None:
            return default
        return self.metadata.get(key, default)

    def add_tag(self, tag: str) -> None:
        """Add a tag"""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)

    def has_tag(self, tag: str) -> bool:
        """Check if has specific tag"""
        return self.tags is not None and tag in self.tags
