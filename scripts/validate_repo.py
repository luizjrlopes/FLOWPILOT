from pathlib import Path
import ast
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {".git", "node_modules", ".next", "__pycache__", ".context-integrity"}

required = [
    "README.md",
    "docker-compose.yml",
    "apps/api/app/main.py",
    "apps/api/app/worker.py",
    "apps/api/app/engine.py",
    "apps/web/package.json",
    "apps/web/src/app/login/page.tsx",
    "docs/architecture.md",
    "apps/api/app/contracts/supplier-request.schema.json",
    "apps/api/app/contracts/supplier-extraction.schema.json",
    "apps/api/app/contracts/risk-assessment.schema.json",
]

errors: list[str] = []


def repository_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        yield path


for relative_path in required:
    if not (ROOT / relative_path).exists():
        errors.append(f"missing {relative_path}")

for path in (ROOT / "apps/api").rglob("*.py"):
    if any(part in IGNORED_DIRS for part in path.relative_to(ROOT).parts):
        continue
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        errors.append(f"python syntax {path.relative_to(ROOT)}:{exc.lineno} {exc.msg}")

try:
    package = json.loads((ROOT / "apps/web/package.json").read_text(encoding="utf-8"))
    if not package.get("dependencies", {}).get("next"):
        errors.append("Next.js dependency missing")
except Exception as exc:
    errors.append(f"package.json: {exc}")

for schema_path in (ROOT / "apps/api/app/contracts").glob("*.json"):
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append(f"unexpected JSON Schema draft: {schema_path.relative_to(ROOT)}")
    except Exception as exc:
        errors.append(f"schema {schema_path.relative_to(ROOT)}: {exc}")

files = list(repository_files())
combined = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in files)
for token in [
    "WAITING_APPROVAL",
    "DLQ",
    "idempotency",
    "ai_invalid",
    "connector_failure",
    "APPROVAL_REQUESTED",
    "RabbitMQ",
]:
    if token.lower() not in combined.lower():
        errors.append(f"missing behavior marker {token}")

if errors:
    print("VALIDATION: FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("VALIDATION: PASS")
print(f"files={len(files)}")
