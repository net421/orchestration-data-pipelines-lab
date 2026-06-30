# Azure Data Factory Pipeline Design Pattern

## Pipeline Stages

1. Ingest source files or API extracts.
2. Land raw data in a storage zone.
3. Trigger transformation notebooks or SQL scripts.
4. Validate record counts and required fields.
5. Publish marts to BI consumption layer.

This is a design pattern document, not a deployed ADF instance.

## Validation-First Mapping

| Local Simulator Task | ADF Equivalent | Review Note |
| --- | --- | --- |
| `extract_raw_orders` | Copy activity | Retry transient source failures only. |
| `validate_raw_orders` | Validation activity or Stored Procedure activity | Fail fast on missing columns, null required fields, or duplicate keys. |
| `clean_orders` | Mapping Data Flow, SQL script, or notebook activity | Standardize types and calculate reusable fields. |
| `validate_clean_orders` | If Condition plus SQL validation query | Stop downstream publish if deterministic data checks fail. |
| `build_order_mart` | Stored Procedure, dbt job, or notebook activity | Create BI-ready table after validation gates pass. |
| `publish_quality_summary` | Web activity, Stored Procedure, or metadata write | Publish run metrics and trigger stakeholder alert assumptions. |

## Monitoring Assumptions

- Pipeline failure alerts route to data engineering.
- Validation failure alerts route to source-data owners and analytics engineering.
- Business exceptions in valid data route to operations stakeholders.
- All retries should be capped and visible in run history.
