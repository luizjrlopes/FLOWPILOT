# Security and control model

Demo JWT sessions are signed by the API. Permissions are enforced server-side:

- **Operador:** read workflows/runs, trigger executions, inspect approvals/DLQ;
- **Aprovador:** read runs and decide pending approvals;
- **Admin de processo:** workflow administration, triggers, approval, DLQ recovery, connectors, audit and reset;
- **Auditor:** read executions and audit only.

The web navigation mirrors these boundaries but is not trusted for authorization.

Webhook triggers require an idempotency key. Repeating a key returns the existing execution instead of creating a duplicate.
