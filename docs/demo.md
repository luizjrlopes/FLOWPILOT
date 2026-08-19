# Demo script

## Happy path

Login Carla Nunes → Workflows → Supplier onboarding → Trigger. Wait for `WAITING_APPROVAL`. Login Diego Moura → Approvals → open run → approve. The worker resumes to `COMPLETED`.

## Connector failure

Login Bianca Prado → Connectors → enable connector failure → trigger supplier workflow. Inspect three retry events and terminal `DLQ`. Disable failure → DLQ → reprocess. Inspect the new run and `parent_run_id`.

## Invalid AI output

Admin enables invalid AI output, triggers a run, and verifies `FAILED_VALIDATION`. No approval request is produced.

## Idempotency

Send the supplier webhook twice with the same `X-Idempotency-Key`. Both responses point to the same `run_id`; the second response marks `duplicate: true`.
