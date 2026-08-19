# FlowPilot AI

FlowPilot AI is a locally runnable workflow automation platform focused on **controlled execution**: declarative YAML workflows, deterministic steps, structured AI output, human approval gates, retries, DLQ recovery, idempotent webhooks, simulated connectors and a complete evidence trail.

The final repository turns the validated HTML prototype into a real application without expanding its scope into a visual workflow builder, ERP, payments, or unsupervised critical automation.

## Final stack

- **Web:** Next.js 16.2.11, React 19.2, TypeScript, App Router
- **API:** Python 3.13, FastAPI 0.140.7, SQLAlchemy 2.0.51
- **Database:** PostgreSQL 18
- **Message broker:** RabbitMQ 4.x, durable quorum queues + explicit DLQ
- **Workflow definitions:** YAML + JSON Schema
- **Structured AI:** provider boundary + Pydantic validation; deterministic local provider by default
- **Auth:** signed JWT demo sessions with server-side RBAC
- **Local runtime:** Docker Compose

No paid service is required for the demo path.

## Product capabilities

- demo login for Operador, Aprovador, Admin de processo and Auditor;
- workflow catalog with versioned YAML definitions;
- creation/update of workflow definitions by Admin;
- manual trigger and idempotent webhook trigger;
- input validation before execution;
- deterministic workflow steps;
- structured AI extraction/classification with validation before state transition;
- connector simulation with retry policy and visible attempts;
- blocking human approval gate;
- safe resume after approval or terminal rejection;
- RabbitMQ worker execution and database-backed state;
- DLQ with explicit reprocessing into a new execution while preserving the original;
- connector health/failure simulation;
- immutable-style execution events and global audit trail;
- repeatable demo reset.

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

Then open:

- Web: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- RabbitMQ management: `http://localhost:15672` (`guest` / `guest`)

The API initializes the schema and seed data. The worker consumes execution messages from RabbitMQ.

## Main demo flow

1. Login as **Carla Nunes / Operador**.
2. Open **Workflows → Onboarding de fornecedor**.
3. Trigger a manual execution.
4. Inspect input validation, structured AI output and connector evidence.
5. The execution stops in `WAITING_APPROVAL`.
6. Login as **Diego Moura / Aprovador**.
7. Approve or reject with a decision reason.
8. If approved, the worker resumes and completes the workflow.

## Failure / DLQ flow

1. Login as **Bianca Prado / Admin de processo**.
2. In **Conectores**, enable the supplier-registry failure scenario.
3. Trigger a workflow execution.
4. The worker records the retry attempts and ends the run in `DLQ`.
5. Restore the connector and open **DLQ**.
6. Reprocess the item. A **new run** is created with `parent_run_id`; the original remains unchanged.

## Invalid AI output flow

Admin can enable the invalid-AI scenario. The local provider then produces an intentionally invalid shape; Pydantic rejects it and the execution ends in `FAILED_VALIDATION` instead of advancing silently.

## Repository layout

```text
apps/
  api/       FastAPI API + workflow engine + RabbitMQ worker
  web/       Next.js user interface
scripts/     deterministic repository checks
docs/        architecture, workflow, security and demo documentation
```

## Validation

Dependency-free checks:

```bash
python scripts/validate_repo.py
python -m unittest discover apps/api/tests -v
```

Full runtime/build validation is covered by CI and Docker Compose once dependencies are installed.
