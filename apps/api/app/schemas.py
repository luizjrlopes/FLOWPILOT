from pydantic import BaseModel, Field

class LoginIn(BaseModel): user_id: str
class WorkflowIn(BaseModel): name: str; version: str; status: str = "Rascunho"; trigger_mode: str = "manual"; description: str = ""; yaml_text: str
class TriggerIn(BaseModel): supplier_name: str; tax_id: str; country: str = "BR"
class DecisionIn(BaseModel): decision: str = Field(pattern="^(approve|reject)$"); reason: str = ""
class FlagIn(BaseModel): enabled: bool
