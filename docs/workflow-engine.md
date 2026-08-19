# Workflow engine

The seeded supplier workflow is YAML and executes seven conceptual steps:

1. validate input;
2. AI structured extraction;
3. AI risk classification;
4. supplier connector with retry policy;
5. blocking human approval;
6. idempotent supplier creation mock;
7. report/evidence generation.

Execution state is persisted after each material boundary. Approval stops worker progress in `WAITING_APPROVAL`. Approval publishes a resume message. Rejection is terminal. Connector retries are recorded as events; exhausted retries move the run to `DLQ` and also publish a DLQ message. Reprocessing creates a new execution with `parent_run_id`.
