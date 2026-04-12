import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    @declared_attr
    def __tablename__(cls: Any) -> str:
        return cls.__name__.lower() + "s"

    def to_dict(self) -> Dict[str, Any]:
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"


class TimestampMixin:
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False, 
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )


class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    created_by = Column(UUID(as_uuid=True), nullable=True, index=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True, index=True)
    audit_metadata = Column(JSON, nullable=True)

    def set_audit_info(
        self, user_id: uuid.UUID, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        if not self.created_by:
            self.created_by = user_id
        self.updated_by = user_id
        if metadata:
            self.audit_metadata = dict(metadata)


class EncryptedMixin:
    encryption_key_id = Column(String(255), nullable=True)
    is_encrypted = Column(Boolean, default=False, nullable=False)

    def mark_encrypted(self, key_id: str) -> None:
        self.is_encrypted = True
        self.encryption_key_id = key_id


class VersionMixin:
    version = Column(Integer, default=1, nullable=False)

    def increment_version(self) -> None:
        self.version += 1


class MetadataMixin:
    extra_metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)

    def add_metadata(self, key: str, value: Any) -> None:
        if self.extra_metadata is None:
            self.extra_metadata = {}
        new_meta = dict(self.extra_metadata)
        new_meta[key] = value
        self.extra_metadata = new_meta

    def get_metadata(self, key: str, default: Any = None) -> Any:
        if self.extra_metadata is None:
            return default
        return self.extra_metadata.get(key, default)

    def add_tag(self, tag: str) -> None:
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            new_tags = list(self.tags)
            new_tags.append(tag)
            self.tags = new_tags

    def remove_tag(self, tag: str) -> None:
        if self.tags and tag in self.tags:
            new_tags = list(self.tags)
            new_tags.remove(tag)
            self.tags = new_tags

    def has_tag(self, tag: str) -> bool:
        return self.tags is not None and tag in self.tags