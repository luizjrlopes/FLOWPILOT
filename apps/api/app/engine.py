from __future__ import annotations
import time
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import ValidationError
from .ai import provider
from .audit import record
from .config import settings
from .domain import parse_workflow, validate_supplier_input, validate_ai_output
from .messaging import publish_dlq
from .models import Approval, Connector, Execution, ExecutionEvent, SystemFlag, Workflow

def event(db: Session, run: Execution, type_: str, detail: str, level: str = "done", metadata: dict | None = None):
    db.add(ExecutionEvent(execution_id=run.id, type=type_, detail=detail, level=level, metadata_json=metadata or {}))

def flag(db: Session, key: str) -> bool:
    item = db.get(SystemFlag, key)
    return bool(item and item.enabled)

def execute(db: Session, run_id: str) -> str:
    run = db.get(Execution, run_id)
    if not run: return "missing"
    workflow = db.get(Workflow, run.workflow_id)
    if not workflow: return "missing-workflow"
    definition = parse_workflow(workflow.yaml_text)
    try:
        supplier = validate_supplier_input(run.input_json)
    except ValidationError as exc:
        run.state = "FAILED_VALIDATION"; run.error = str(exc); event(db, run, "INPUT_INVALID", "Input rejected by schema", "failed"); db.commit(); return run.state

    if run.state in {"QUEUED", "RUNNING"}:
        run.state = "RUNNING"; run.current_step = 1
        event(db, run, "INPUT_VALIDATED", "Schema de entrada válido")
        invalid = flag(db, "ai_invalid")
        ai = provider(invalid=invalid)
        extraction = ai.extract(supplier.supplier_name)
        try:
            extracted, risk = validate_ai_output(extraction, ai.classify_risk(extraction.get("annual_value", 0) if isinstance(extraction, dict) else 0))
        except Exception as exc:
            run.state = "FAILED_VALIDATION"; run.error = str(exc); run.current_step = 2
            event(db, run, "AI_OUTPUT_INVALID", "Saída estruturada da IA rejeitada pelo contrato", "failed")
            record(db, actor="AI Step", action="STRUCTURED_OUTPUT_REJECTED", entity_type="RUN", entity_id=run.id, details="AI output failed validation")
            db.commit(); return run.state
        run.ai_json = {"extracted": extracted.model_dump(), "risk": risk.model_dump()}; run.current_step = 3
        event(db, run, "AI_EXTRACTION_VALID", "Saída JSON validada contra contrato")
        record(db, actor="AI Step", action="STRUCTURED_OUTPUT_VALIDATED", entity_type="RUN", entity_id=run.id, details="supplier extraction + risk assessment")

        connector = db.get(Connector, "supplier-registry")
        failing = flag(db, "connector_failure")
        for attempt in range(1, 4):
            connector.calls += 1
            if not failing:
                event(db, run, "CONNECTOR_SUCCEEDED", f"Supplier Registry Mock respondeu 200 na tentativa {attempt}", metadata={"attempt": attempt}); break
            connector.failures += 1; run.retry_count = attempt
            event(db, run, f"CONNECTOR_RETRY_{attempt}", f"Tentativa {attempt}/3 retornou 503", "warn", {"backoff_seconds": 2 ** (attempt-1)})
            time.sleep(min(settings.worker_retry_delay_seconds * (2 ** (attempt-1)), 0.2))
        else:
            run.state = "DLQ"; run.error = "Supplier Registry Mock unavailable after 3 attempts"; run.current_step = 3
            event(db, run, "MOVED_TO_DLQ", "Retries esgotados; execução suspensa", "failed")
            record(db, actor="FlowPilot", action="DLQ_ENQUEUED", entity_type="RUN", entity_id=run.id, details=run.error)
            db.commit(); publish_dlq(run.id, run.error); return run.state

        run.state = "WAITING_APPROVAL"; run.current_step = 4
        event(db, run, "APPROVAL_REQUESTED", "Execução bloqueada aguardando aprovador", "active")
        record(db, actor="FlowPilot", action="APPROVAL_REQUESTED", entity_type="RUN", entity_id=run.id, details="required_role=approver")
        db.commit(); return run.state

    if run.state == "APPROVED":
        approval = db.scalar(select(Approval).where(Approval.execution_id == run.id))
        run.current_step = 5
        event(db, run, "CREATE_SUPPLIER_SUCCEEDED", "Cadastro simulado concluído com chave idempotente")
        run.current_step = 6
        run.result_json = {"supplier": run.ai_json.get("extracted", {}), "risk": run.ai_json.get("risk", {}), "approval": {"by": approval.decided_by if approval else "unknown", "reason": approval.reason if approval else ""}, "evidence": [e.type for e in run.events]}
        event(db, run, "REPORT_GENERATED", "Relatório e evidências registrados")
        run.state = "COMPLETED"
        event(db, run, "RUN_COMPLETED", "Workflow concluído")
        record(db, actor="FlowPilot Worker", action="RUN_COMPLETED", entity_type="RUN", entity_id=run.id, details="workflow completed after approval")
        db.commit(); return run.state

    return run.state
