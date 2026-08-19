import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from app.domain import (
    ContractValidationError,
    can,
    can_decide,
    can_reprocess,
    contract_schema,
    parse_workflow,
    retry_delays,
    validate_ai_output,
    validate_supplier_input,
)

class DomainTests(unittest.TestCase):
    def test_roles_are_strict(self):
        self.assertTrue(can("operator","executions:trigger")); self.assertFalse(can("operator","approvals:decide")); self.assertTrue(can("admin","dlq:retry")); self.assertFalse(can("auditor","executions:trigger"))
    def test_approval_gate(self):
        self.assertTrue(can_decide("WAITING_APPROVAL")); self.assertFalse(can_decide("RUNNING"))
    def test_dlq_reprocess_gate(self):
        self.assertTrue(can_reprocess("DLQ")); self.assertFalse(can_reprocess("FAILED"))
    def test_retry_backoff(self): self.assertEqual(retry_delays(3),[1.0,2.0,4.0])
    def test_supplier_input(self): self.assertEqual(validate_supplier_input({"supplier_name":"Atlas","tax_id":"12345","country":"BR"}).country,"BR")
    def test_invalid_supplier_input_is_rejected_by_json_schema(self):
        with self.assertRaises(ContractValidationError): validate_supplier_input({"supplier_name":"A","tax_id":"1","country":"Brazil"})
    def test_invalid_ai_output_is_rejected_by_json_schema(self):
        with self.assertRaises(ContractValidationError): validate_ai_output({"legal_name":17,"annual_value":"x"},{"risk":"unknown","score":4,"reasons":[]})
    def test_contract_files_are_loadable(self):
        self.assertEqual(contract_schema("supplier-request.schema.json")["type"], "object")
    def test_yaml_definition(self):
        text = "id: demo\nversion: '1'\ntrigger: {manual: true}\ninput_schema: supplier-request.schema.json\nsteps: []\n"
        w=parse_workflow(text); self.assertEqual(w.id,"demo")
if __name__=="__main__": unittest.main()
