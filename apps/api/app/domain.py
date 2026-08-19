from __future__ import annotations
from importlib.resources import files
import json
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JSONSchemaValidationError
from pydantic import BaseModel, Field
import yaml

ROLE_PERMISSIONS = {
    "operator": {"dashboard:read", "workflows:read", "executions:read", "executions:trigger", "approvals:read", "dlq:read"},
    "approver": {"dashboard:read", "executions:read", "approvals:read", "approvals:decide"},
    "admin": {"dashboard:read", "workflows:read", "workflows:write", "executions:read", "executions:trigger", "approvals:read", "approvals:decide", "dlq:read", "dlq:retry", "connectors:read", "connectors:write", "audit:read", "demo:reset"},
    "auditor": {"dashboard:read", "executions:read", "audit:read"},
}

TERMINAL_STATES = {"COMPLETED", "REJECTED", "FAILED", "FAILED_VALIDATION", "DLQ"}

class ContractValidationError(ValueError):
    pass

class SupplierInput(BaseModel):
    supplier_name: str = Field(min_length=2)
    tax_id: str = Field(min_length=5)
    country: str = Field(pattern="^[A-Z]{2}$")

class SupplierExtraction(BaseModel):
    legal_name: str
    category: str
    annual_value: int = Field(ge=0)

class RiskAssessment(BaseModel):
    risk: str = Field(pattern="^(low|medium|high)$")
    score: float = Field(ge=0, le=1)
    reasons: list[str] = Field(min_length=1)

class WorkflowDefinition(BaseModel):
    id: str
    version: str
    trigger: dict[str, Any]
    input_schema: str
    steps: list[dict[str, Any]]

def can(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())

def contract_schema(name: str) -> dict[str, Any]:
    resource = files("app.contracts").joinpath(name)
    return json.loads(resource.read_text(encoding="utf-8"))

def validate_contract(name: str, payload: dict[str, Any]) -> None:
    validator = Draft202012Validator(contract_schema(name))
    errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
    if errors:
        first = errors[0]
        path = ".".join(str(part) for part in first.path) or "$"
        raise ContractValidationError(f"{name}:{path}: {first.message}")

def parse_workflow(text: str) -> WorkflowDefinition:
    raw = yaml.safe_load(text)
    return WorkflowDefinition.model_validate(raw)

def validate_supplier_input(payload: dict) -> SupplierInput:
    validate_contract("supplier-request.schema.json", payload)
    return SupplierInput.model_validate(payload)

def validate_ai_output(extraction: dict, risk: dict) -> tuple[SupplierExtraction, RiskAssessment]:
    validate_contract("supplier-extraction.schema.json", extraction)
    validate_contract("risk-assessment.schema.json", risk)
    return SupplierExtraction.model_validate(extraction), RiskAssessment.model_validate(risk)

def retry_delays(max_attempts: int, base: float = 1.0) -> list[float]:
    return [base * (2 ** i) for i in range(max_attempts)]

def can_decide(state: str) -> bool:
    return state == "WAITING_APPROVAL"

def can_reprocess(state: str) -> bool:
    return state == "DLQ"
