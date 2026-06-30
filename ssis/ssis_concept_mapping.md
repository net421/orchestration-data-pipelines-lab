# SSIS Concept Mapping

| SSIS Concept | Modern Pipeline Equivalent |
|---|---|
| Control Flow | DAG / orchestration graph |
| Data Flow Task | transformation task / dbt model / Spark job |
| Connection Manager | source/target connection config |
| Package Parameters | environment variables / secrets |
| Event Handlers | error handling and alerting hooks |

## Validation-First Mapping

| SSIS Pattern | Local Simulator Equivalent | Why It Matters |
| --- | --- | --- |
| Precedence constraints | `depends_on` task graph | Makes task order explicit and reviewable. |
| Data Flow row count checks | `require_positive_row_count` | Prevents empty extracts from reaching marts. |
| Derived Column / Data Conversion | `clean_orders` | Converts raw strings into modeled analytics fields. |
| Conditional Split for rejects | validation failure path | Separates deterministic bad data from retryable platform failures. |
| Event Handler on failure | validation and retry logging | Captures task id, attempt count, and failure reason. |
| Execute SQL Task | mart build / quality summary | Publishes BI-ready outputs after validation gates pass. |
