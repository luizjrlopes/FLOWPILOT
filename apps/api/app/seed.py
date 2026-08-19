from sqlalchemy import delete
from sqlalchemy.orm import Session
from .models import Approval, AuditEvent, Connector, Execution, ExecutionEvent, SystemFlag, User, WebhookReceipt, Workflow

SUPPLIER_YAML = """id: supplier-onboarding
version: '1.4'
trigger:
  manual: true
  webhook: /hooks/supplier
input_schema: supplier-request.schema.json
steps:
  - id: validate_input
    type: validate
  - id: extract_documents
    type: ai.structured
    output_schema: supplier-extraction.schema.json
  - id: classify_risk
    type: ai.structured
    output_schema: risk-assessment.schema.json
  - id: supplier_api
    type: connector.mock
    retry:
      max_attempts: 3
      backoff: exponential
  - id: human_approval
    type: approval
    required_role: approver
  - id: create_supplier
    type: connector.mock
    idempotency: required
  - id: generate_report
    type: report
"""
ACCESS_YAML = """id: access-review
version: '2.0'
trigger: {manual: true}
input_schema: generic
steps: []
"""

INVOICE_YAML = """id: invoice-triage
version: '0.9'
trigger: {webhook: /hooks/invoice}
input_schema: generic
steps: []
"""


def reset_demo(db: Session):
    for model in [Approval, ExecutionEvent, WebhookReceipt, AuditEvent, Execution, SystemFlag, Connector, Workflow, User]:
        db.execute(delete(model))
    db.commit(); seed(db)

def seed(db: Session):
    if db.get(User, "u1"): return
    db.add_all([
        User(id="u1", name="Carla Nunes", role="operator"),
        User(id="u2", name="Marcos Leal", role="operator"),
        User(id="u3", name="Diego Moura", role="approver"),
        User(id="u4", name="Bianca Prado", role="admin"),
        User(id="u5", name="Rafael Tavares", role="auditor"),
    ])
    db.add_all([
        Workflow(id="WF-SUPPLIER-ONBOARDING", name="Onboarding de fornecedor", version="v1.4", status="Ativo", trigger_mode="manual + webhook", execution_count=182, description="Valida cadastro, executa IA estruturada, consulta API simulada, exige aprovação humana e gera evidências.", yaml_text=SUPPLIER_YAML),
        Workflow(id="WF-ACCESS-REVIEW", name="Revisão periódica de acessos", version="v2.0", status="Ativo", trigger_mode="manual", execution_count=74, description="Consolida acessos simulados, identifica inconsistências e exige decisão humana.", yaml_text=ACCESS_YAML),
        Workflow(id="WF-INVOICE-TRIAGE", name="Triagem documental", version="v0.9", status="Rascunho", trigger_mode="webhook", execution_count=18, description="Extrai campos estruturados e encaminha inconsistências para revisão.", yaml_text=INVOICE_YAML),
    ])
    db.add_all([
        Connector(id="supplier-registry", name="Supplier Registry Mock", kind="REST", status="Saudável", calls=241, failures=3),
        Connector(id="erp-adapter", name="ERP Adapter Mock", kind="REST", status="Saudável", calls=132, failures=0),
        Connector(id="mail", name="Notification Mailer", kind="EMAIL", status="Saudável", calls=96, failures=1),
        Connector(id="storage", name="Evidence Storage Mock", kind="STORAGE", status="Saudável", calls=418, failures=0),
        SystemFlag(key="connector_failure", enabled=False), SystemFlag(key="ai_invalid", enabled=False),
    ])
    r1=Execution(id="RUN-02841",workflow_id="WF-SUPPLIER-ONBOARDING",state="WAITING_APPROVAL",trigger="manual",actor_name="Carla Nunes",input_json={"supplier_name":"Atlas Components","tax_id":"00.000.000/0001-00","country":"BR"},ai_json={"extracted":{"legal_name":"Atlas Components Ltda.","category":"Industrial","annual_value":280000},"risk":{"risk":"medium","score":0.72,"reasons":["empresa recente","documentação consistente"]}},current_step=4)
    r1.events=[ExecutionEvent(type="TRIGGER_RECEIVED",detail="Execução manual iniciada por Carla Nunes"),ExecutionEvent(type="INPUT_VALIDATED",detail="Schema de entrada válido"),ExecutionEvent(type="AI_EXTRACTION_VALID",detail="Saída JSON validada contra contrato"),ExecutionEvent(type="CONNECTOR_SUCCEEDED",detail="Supplier Registry Mock respondeu 200"),ExecutionEvent(type="APPROVAL_REQUESTED",detail="Execução bloqueada aguardando aprovador",level="active")]
    r2=Execution(id="RUN-02840",workflow_id="WF-SUPPLIER-ONBOARDING",state="COMPLETED",trigger="webhook",actor_name="Webhook",input_json={"supplier_name":"Nova Freight","tax_id":"11.111.111/0001-11","country":"BR"},retry_count=1,current_step=6,result_json={"status":"completed"})
    r2.events=[ExecutionEvent(type="WEBHOOK_ACCEPTED",detail="Idempotency key reconhecida"),ExecutionEvent(type="CONNECTOR_RETRY_1",detail="Primeira tentativa recebeu 503; retry agendado",level="warn"),ExecutionEvent(type="APPROVED",detail="Aprovado por Diego Moura"),ExecutionEvent(type="RUN_COMPLETED",detail="Relatório e evidências registrados")]
    r3=Execution(id="RUN-02836",workflow_id="WF-SUPPLIER-ONBOARDING",state="DLQ",trigger="manual",actor_name="Marcos Leal",input_json={"supplier_name":"Orion Services","tax_id":"22.222.222/0001-22","country":"BR"},retry_count=3,current_step=3,error="Supplier Registry Mock unavailable after 3 attempts")
    r3.events=[ExecutionEvent(type="INPUT_VALIDATED",detail="Entrada válida"),ExecutionEvent(type="AI_EXTRACTION_VALID",detail="JSON estruturado válido"),ExecutionEvent(type="CONNECTOR_RETRY_1",detail="Retry 1/3 falhou",level="warn"),ExecutionEvent(type="CONNECTOR_RETRY_2",detail="Retry 2/3 falhou",level="warn"),ExecutionEvent(type="CONNECTOR_RETRY_3",detail="Retry 3/3 falhou",level="failed"),ExecutionEvent(type="MOVED_TO_DLQ",detail="Execução suspensa para intervenção segura",level="failed")]
    db.add_all([r1,r2,r3])
    db.add_all([
        AuditEvent(actor="FlowPilot",action="APPROVAL_REQUESTED",entity_type="RUN",entity_id="RUN-02841",details="workflow bloqueado; role=approver"),
        AuditEvent(actor="Supplier Registry Mock",action="CONNECTOR_RESPONSE",entity_type="RUN",entity_id="RUN-02841",details="HTTP 200 · 184ms"),
        AuditEvent(actor="AI Step",action="STRUCTURED_OUTPUT_VALIDATED",entity_type="RUN",entity_id="RUN-02841",details="risk assessment + supplier extraction"),
        AuditEvent(actor="Diego Moura",action="APPROVAL_GRANTED",entity_type="RUN",entity_id="RUN-02840",details="decision=approve"),
        AuditEvent(actor="FlowPilot",action="DLQ_ENQUEUED",entity_type="RUN",entity_id="RUN-02836",details="connector retries exhausted"),
    ])
    db.commit()
