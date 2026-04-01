"""
Audit logging middleware and utility functions
"""

import logging
from typing import Optional

from models.compliance import AuditEventType, AuditLog
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def audit_log(
    db: AsyncSession,
    user_id: Optional[str],
    event_name: str,
    entity_type: str,
    entity_id: str,
    changes: Optional[dict] = None,
    ip_address: Optional[str] = None,
    event_type: AuditEventType = AuditEventType.SYSTEM_EVENT,
) -> None:
    """
    Create an audit log entry
    """
    try:
        log_entry = AuditLog(
            user_id=user_id,
            event_type=event_type,
            event_name=event_name,
            event_description=f"{event_name} on {entity_type}:{entity_id}",
            entity_type=entity_type,
            entity_id=entity_id,
            extra_metadata=changes,
            ip_address=ip_address,
        )
        db.add(log_entry)
        await db.commit()
        logger.info(f"Audit log created: {event_name} for {entity_type}:{entity_id}")
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        # Don't fail the request if audit logging fails
