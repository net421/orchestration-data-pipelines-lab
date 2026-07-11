# Validation Summary

The release gate is `make verify`. It regenerates all eight synthetic source files and executes four operational scenarios plus pytest.

## Local verification

- 8 deterministic source files generated.
- 120 orders and 240 order lines.
- 11 source/output quality checks passed.
- Unit fill rate: 98.13%.
- Complete-order rate: 80.00%.
- On-time delivery: 36.67%.
- OTIF: 29.17%.
- Initial publication succeeded.
- Second publication was byte-identical and marked idempotent.
- A missing required column failed at `validate_sources`.
- The failed run wrote failure metadata without replacing `runs/latest.json`.
- Published outputs remained unchanged during the rejected run.
- Restoring the source contract produced a successful recovery run.
- 4 pytest tests passed.

GitHub Actions regenerates `validation/generated/scenario_report.json` and uploads it as `orchestration-validation-evidence` before merge.
