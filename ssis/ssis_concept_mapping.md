# SSIS Concept Mapping

| SSIS Concept | This Lab | Modern Equivalent |
|---|---|---|
| Control Flow | Pipeline stages | Airflow DAG / Prefect flow / ADF pipeline |
| Data Flow Task | `transform.py` | Spark/dbt/Python transformation |
| Connection Manager | `PipelineConfig` | Resource, connection, linked service |
| Precedence Constraint | Validation before publish | DAG dependency / quality gate |