# Alerting Strategy

## Page Immediately

- pipeline cannot ingest required source files;
- data-contract validation fails;
- published row count unexpectedly becomes zero;
- OTIF or fill-rate output leaves the valid 0–1 range;
- publication cannot be completed atomically.

## Notify During Business Hours

- processing duration exceeds the expected SLA;
- source row counts move outside a historical tolerance;
- output hashes remain unchanged when a new source delivery was expected;
- repeated retries indicate upstream instability.

Alerts should include run ID, failing stage, exception class, source date, and a
link or path to run metadata. Do not alert on every successful retry.
