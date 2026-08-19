from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def now(): return datetime.now(timezone.utc)
def uid(prefix: str): return f"{prefix}-{uuid4().hex[:8].upper()}"

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    role: Mapped[str] = mapped_column(String(40), index=True)

class Workflow(Base):
    __tablename__ = "workflows"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    version: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="Rascunho")
    trigger_mode: Mapped[str] = mapped_column(String(80), default="manual")
    description: Mapped[str] = mapped_column(Text, default="")
    yaml_text: Mapped[str] = mapped_column(Text)
    execution_count: Mapped[int] = mapped_column(Integer, default=0)

class Execution(Base):
    __tablename__ = "executions"
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: uid("RUN"))
    workflow_id: Mapped[str] = mapped_column(ForeignKey("workflows.id"), index=True)
    state: Mapped[str] = mapped_column(String(40), index=True, default="QUEUED")
    trigger: Mapped[str] = mapped_column(String(30))
    actor_name: Mapped[str] = mapped_column(String(120))
    input_json: Mapped[dict] = mapped_column(JSON, default=dict)
    ai_json: Mapped[dict] = mapped_column(JSON, default=dict)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    parent_run_id: Mapped[str | None] = mapped_column(ForeignKey("executions.id"), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    events: Mapped[list[ExecutionEvent]] = relationship(back_populates="execution", cascade="all, delete-orphan", order_by="ExecutionEvent.created_at")

class ExecutionEvent(Base):
    __tablename__ = "execution_events"
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: uid("EVT"))
    execution_id: Mapped[str] = mapped_column(ForeignKey("executions.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(80), index=True)
    detail: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(20), default="done")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    execution: Mapped[Execution] = relationship(back_populates="events")

class Approval(Base):
    __tablename__ = "approvals"
    __table_args__ = (UniqueConstraint("execution_id", name="uq_approval_execution"),)
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: uid("APR"))
    execution_id: Mapped[str] = mapped_column(ForeignKey("executions.id"), index=True)
    decision: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text, default="")
    decided_by: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Connector(Base):
    __tablename__ = "connectors"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), default="Saudável")
    calls: Mapped[int] = mapped_column(Integer, default=0)
    failures: Mapped[int] = mapped_column(Integer, default=0)

class WebhookReceipt(Base):
    __tablename__ = "webhook_receipts"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_webhook_idempotency"),)
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: uid("WH"))
    idempotency_key: Mapped[str] = mapped_column(String(160), index=True)
    execution_id: Mapped[str] = mapped_column(ForeignKey("executions.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: uid("AUD"))
    actor: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[str] = mapped_column(String(80), index=True)
    details: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class SystemFlag(Base):
    __tablename__ = "system_flags"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
