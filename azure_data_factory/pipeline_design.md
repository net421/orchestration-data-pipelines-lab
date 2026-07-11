# Azure Data Factory Design Pattern

This design maps the local pipeline to an Azure implementation without
claiming a deployed production environment.

## Azure Components

- ADLS Gen2 `raw`, `validated`, and `published` zones.
- Managed Identity for service-to-service authentication.
- Key Vault for secrets that cannot use managed identity.
- Parameterized datasets for environment, source date, and file path.
- Copy Activity for landing ERP/TMS extracts.
- Azure Function, Databricks Notebook, or Synapse Notebook for Python logic.
- Stored Procedure or SQL Script activity for reconciliation checks.
- If Condition quality gate before publication.
- Azure Monitor / Log Analytics for run telemetry.

## Control Flow

1. `CopyOrdersToRaw`
2. `CopyShipmentsToRaw`
3. `ValidateDataContracts`
4. `IfValidationPassed`
5. `TransformOrderServiceMarts`
6. `RunQualityChecks`
7. `PublishMarts`
8. `WriteRunMetadata`

Failure paths send an alert and retain the invalid landing files for inspection.
