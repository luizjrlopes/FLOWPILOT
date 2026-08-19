from sqlalchemy.orm import Session
from .models import AuditEvent, User

def record(db: Session, *, actor: str, action: str, entity_type: str, entity_id: str, details: str, metadata: dict | None = None):
    db.add(AuditEvent(actor=actor, action=action, entity_type=entity_type, entity_id=entity_id, details=details, metadata_json=metadata or {}))
