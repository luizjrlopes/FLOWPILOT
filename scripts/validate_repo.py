from pathlib import Path
import json, sys, ast
root=Path(__file__).resolve().parents[1]
required=["README.md","docker-compose.yml","apps/api/app/main.py","apps/api/app/worker.py","apps/api/app/engine.py","apps/web/package.json","apps/web/src/app/login/page.tsx","docs/architecture.md","apps/api/app/contracts/supplier-request.schema.json","apps/api/app/contracts/supplier-extraction.schema.json","apps/api/app/contracts/risk-assessment.schema.json"]
errors=[]
for p in required:
    if not (root/p).exists(): errors.append(f"missing {p}")
for p in (root/"apps/api").rglob("*.py"):
    try: ast.parse(p.read_text())
    except SyntaxError as e: errors.append(f"python syntax {p.relative_to(root)}:{e.lineno} {e.msg}")
try:
    pkg=json.loads((root/"apps/web/package.json").read_text())
    if pkg["dependencies"].get("next")!="16.2.11": errors.append("unexpected Next.js version")
except Exception as e:
    errors.append(f"package.json: {e}")

for schema_path in (root/"apps/api/app/contracts").glob("*.json"):
    try:
        schema=json.loads(schema_path.read_text())
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema": errors.append(f"unexpected JSON Schema draft: {schema_path.relative_to(root)}")
    except Exception as e:
        errors.append(f"schema {schema_path.relative_to(root)}: {e}")
combined="\n".join(p.read_text(errors="ignore") for p in root.rglob("*") if p.is_file() and ".context-integrity" not in p.parts)
for token in ["WAITING_APPROVAL","DLQ","idempotency","ai_invalid","connector_failure","APPROVAL_REQUESTED","RabbitMQ"]:
    if token.lower() not in combined.lower(): errors.append(f"missing behavior marker {token}")
if errors:
    print("VALIDATION: FAIL")
    print("\n".join(errors))
    sys.exit(1)
print("VALIDATION: PASS")
print("files=",sum(1 for p in root.rglob("*") if p.is_file() and ".context-integrity" not in p.parts))
