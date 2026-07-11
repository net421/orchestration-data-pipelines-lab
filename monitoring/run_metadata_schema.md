# Run Metadata Schema

Every run records:

```json
{
  "run_id": "unique identifier",
  "status": "SUCCESS or FAILED",
  "started_at_utc": "ISO-8601 timestamp",
  "completed_at_utc": "ISO-8601 timestamp",
  "duration_seconds": 0.0,
  "input_rows": {"orders": 0, "shipments": 0},
  "published_artifacts": [
    {"path": "file.csv", "rows": 0, "sha256": "content hash"}
  ],
  "quality_checks": [
    {"check_name": "name", "status": "PASS", "detail": "explanation"}
  ],
  "idempotent_same_as_previous": false
}
```

This supports auditability, debugging, SLA reporting, and downstream lineage.
