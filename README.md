# Orchestration Data Pipelines Lab

Pipeline orchestration patterns across modern and enterprise ETL tools: Airflow, Prefect, Dagster, Azure Data Factory, and SSIS concepts.

This is a portfolio lab. It demonstrates orchestration patterns, validation gates, retry assumptions, and tool mappings without claiming production ownership of any orchestrator.

## Skills Demonstrated

- DAG/flow/asset thinking
- raw → clean → modeled → reporting pipeline design
- logging, retry and error-handling patterns
- enterprise ETL concept mapping

## Featured Artifact: Validation-First Pipeline

| File | What it proves |
| --- | --- |
| `shared/local_pipeline_simulator.py` | Runnable orchestration contract with dependencies, validation gates, retry policy, lineage, and publish summary. |
| `airflow/dags/raw_to_mart_dag.py` | Airflow-style DAG structure with retries and framework-light import fallback. |
| `prefect/flows/raw_to_mart_flow.py` | Prefect-style task/flow mapping that can run locally without Prefect installed. |
| `shared/error_handling.py` | Reusable validation helpers for deterministic data quality failures. |
| `shared/retry_patterns.md` | Retry, alerting, idempotency, and validation-failure review guidance. |
| `docs/validation_first_orchestration.md` | Lineage diagram, validation contract, tool mapping, and local review criteria. |

## Local Validation

```bash
python shared/local_pipeline_simulator.py
```

Expected summary:

- 6 successful tasks
- 4 quality checks
- 3 mart rows
- fill rate `0.9556`
- 1 service exception

## Hiring Manager Readout

This repo shows orchestration thinking beyond simple task stubs: it distinguishes retryable platform failures from deterministic data quality failures, documents how validation gates protect BI outputs, and maps the same workflow across Airflow, Prefect, Dagster, Azure Data Factory, and SSIS concepts.
