# FlowPilot AI

[English](README.md) | [Português](README.pt-BR.md)

**FlowPilot AI** is a workflow-automation platform designed around controlled execution, traceability and human approval. It combines declarative YAML definitions, asynchronous processing, deterministic steps, structured AI integration, retry policies, a DLQ and a complete evidence trail.

The architecture keeps critical decisions under application control: AI can extract, classify and structure information, but it cannot bypass contracts, approve protected steps or silently mutate execution state.

## Overview

Core capabilities include:

- versioned YAML workflow definitions;
- workflow creation and updates with contract validation;
- manual and idempotent webhook triggers;
- input validation before execution;
- deterministic transformation and decision steps;
- AI extraction and classification with structured output;
- Pydantic validation before AI-dependent state transitions;
- decoupled connectors with retry policies;
- human-approval gates that actually block execution;
- safe resume after approval;
- terminal rejection with a recorded reason;
- asynchronous processing with RabbitMQ;
- Dead Letter Queue with explicit reprocessing;
- creation of a new execution when reprocessing DLQ items while preserving the original run;
- idempotency for external triggers;
- controlled simulation of connector failures and invalid AI output;
- per-run event history and global auditability.

## Architecture

```text
Browser / Next.js
        │ JWT
        ▼
FastAPI API
        │
        ├── Workflow definitions / JSON Schema
        ├── RBAC / idempotency / approvals
        ├── execution state + audit events
        │
        ├──────────────► PostgreSQL
        │
        └── publish ───► RabbitMQ
                            │
                            ▼
                       Python Worker
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
          deterministic   structured   connectors
             steps           AI        / retries
```

The API owns authorization, contracts, run creation, human decisions and state persistence. The worker executes asynchronous steps and publishes evidence for each attempt. RabbitMQ decouples execution from the HTTP request lifecycle and keeps the operational queue explicit.

## Stack

| Layer | Technology |
|---|---|
| Web | Next.js 16.3, React 19, TypeScript, App Router |
| API | Python 3.13, FastAPI, SQLAlchemy 2 |
| Database | PostgreSQL 18 |
| Messaging | RabbitMQ 4, durable queues and DLQ |
| Workflows | YAML + JSON Schema Draft 2020-12 |
| Structured AI | Provider boundary + Pydantic |
| Authentication | JWT + server-side RBAC |
| Local runtime | Docker Compose |
| CI | GitHub Actions |

## Execution model

```text
TRIGGERED
   │
   ▼
INPUT_VALIDATION
   │
   ▼
PROCESSING
   │
   ├──► AI STRUCTURED STEP
   │          │
   │          └── invalid output ──► FAILED_VALIDATION
   │
   ├──► CONNECTOR
   │          │
   │          ├── retry
   │          └── terminal failure ──► DLQ
   │
   ▼
WAITING_APPROVAL
   │
   ├── rejected ──► REJECTED
   │
   └── approved
          │
          ▼
       RESUMED
          │
          ▼
       COMPLETED
```

## Human approval

When a run enters `WAITING_APPROVAL`, the worker does not continue until an authorized user records a decision. The decision, actor, reason and timestamp remain associated with the execution for auditing.

## Structured AI

AI integration follows a provider boundary and requires structured responses. Output is validated before it is accepted by the engine. Contract-incompatible output ends in `FAILED_VALIDATION` instead of advancing silently.

## Retry and DLQ

Transient connector failures follow an explicit retry policy. When retries are exhausted, the run ends in `DLQ`. Reprocessing creates a new run linked through `parent_run_id`, preserving the original execution history.

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

- Web: `http://localhost:3000`
- API: `http://localhost:8000/docs`
- RabbitMQ Management: `http://localhost:15672`

## Repository structure

```text
apps/
├── api/
│   ├── app/
│   │   ├── contracts/
│   │   ├── engine.py
│   │   ├── worker.py
│   │   └── ...
│   └── tests/
└── web/
    └── src/
        └── app/
docs/
scripts/
```

## Validation

```bash
python scripts/validate_repo.py
python -m unittest discover apps/api/tests -v
cd apps/web
npm ci
npm run typecheck
npm run build
```

GitHub Actions runs repository validation, backend tests, deterministic web dependency installation, security auditing, typechecking and production builds.

## Project principles

- **controlled execution**;
- **human-in-the-loop**;
- **contracts before automation**;
- **verifiable AI**;
- **explicit recovery**;
- **idempotency**;
- **auditability**.
