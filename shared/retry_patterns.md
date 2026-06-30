# Retry Patterns

- Retry transient network/API failures.
- Do not retry deterministic validation failures without correction.
- Log attempt count and final failure reason.
- Keep idempotent outputs to avoid duplicate records.

## Portfolio Pattern

The local simulator in `shared/local_pipeline_simulator.py` treats extraction as retryable and validation as deterministic:

| Failure Type | Retry? | Response |
| --- | --- | --- |
| Temporary source timeout | Yes | Retry with capped attempts and log each attempt. |
| Missing required column | No | Fail fast and alert data owner. |
| Duplicate business key | No | Fail fast and quarantine bad extract. |
| Publish timeout after mart build | Yes, if idempotent | Retry publish operation without rebuilding duplicate rows. |
| Service exception in valid data | No pipeline failure | Publish KPI summary and route to stakeholder alert/queue. |

## Review Criteria

- A retry should not hide deterministic bad data.
- Attempt count, task id, and failure reason should be visible in logs.
- Reruns should be safe for downstream marts and reports.
- Alerting assumptions should distinguish platform failure from business exception.
