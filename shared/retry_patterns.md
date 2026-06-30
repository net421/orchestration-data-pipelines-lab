# Retry Patterns

- Retry transient network/API failures.
- Do not retry deterministic validation failures without correction.
- Log attempt count and final failure reason.
- Keep idempotent outputs to avoid duplicate records.
