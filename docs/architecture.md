# Architecture and Design Decisions

## Shared-Core Principle

Airflow, Prefect, Dagster, and ADF should orchestrate the same tested business
logic. Framework-specific code remains thin, which reduces lock-in and avoids
inconsistent KPI implementations.

## Stage Contracts

| Stage | Input | Output | Failure Rule |
|---|---|---|---|
| Ingest | Raw CSV files | DataFrames | Missing file fails |
| Validate | Source DataFrames | Quality results | Contract violation fails |
| Transform | Validated sources | Order and KPI marts | Unexpected schema fails |
| Quality gate | Marts | PASS/FAIL report | Failed check blocks publish |
| Publish | Validated marts | Atomic CSV outputs | I/O failure fails |
| Metadata | Run results | JSON record | Must be written for success |

## Idempotency

Given identical source files and pipeline code:

- published CSV contents are deterministic;
- SHA-256 hashes remain identical;
- the second run records `idempotent_same_as_previous=true`;
- publication uses atomic file replacement to prevent partial outputs.
