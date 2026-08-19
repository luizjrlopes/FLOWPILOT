# Architecture

FlowPilot uses a deliberately small distributed topology:

```text
Next.js web
   ↓ HTTPS/JSON
FastAPI API ───── PostgreSQL 18
   │                 ↑
   └─ publish ─→ RabbitMQ 4.x
                    ↓
                  Worker
                    ↓
       workflow engine / connectors / AI
```

The API owns authentication, authorization, definitions, trigger acceptance, idempotency and human decisions. The worker owns asynchronous workflow execution. PostgreSQL is the source of truth for execution state and evidence; RabbitMQ transports work, not truth.

## Why RabbitMQ here

Retry, worker decoupling and DLQ are first-class product concerns rather than incidental background jobs. A broker makes those behaviors inspectable and independently operable. The local Compose stack uses durable quorum queues.

## AI boundary

AI is allowed to extract/classify structured data. Output is validated before state may advance. The provider cannot approve critical actions, mutate workflow definitions, or bypass an approval gate.
