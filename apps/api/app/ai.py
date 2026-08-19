from __future__ import annotations
from dataclasses import dataclass

class AIProvider:
    def extract(self, supplier_name: str) -> dict: raise NotImplementedError
    def classify_risk(self, annual_value: int) -> dict: raise NotImplementedError

class LocalDeterministicProvider(AIProvider):
    def __init__(self, invalid: bool = False): self.invalid = invalid
    def extract(self, supplier_name: str) -> dict:
        if self.invalid: return {"legal_name": 17, "annual_value": "unknown"}
        return {"legal_name": f"{supplier_name} Ltda.", "category": "Industrial", "annual_value": 210000}
    def classify_risk(self, annual_value: int) -> dict:
        if self.invalid: return {"risk": "unknown", "score": 4, "reasons": []}
        risk = "medium" if annual_value >= 200000 else "low"
        return {"risk": risk, "score": 0.76 if risk == "medium" else 0.91, "reasons": ["cadastro consistente", "documentação demonstrativa válida"]}

def provider(invalid: bool = False) -> AIProvider:
    return LocalDeterministicProvider(invalid=invalid)
