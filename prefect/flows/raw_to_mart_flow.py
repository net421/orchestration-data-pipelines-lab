"""Prefect-style flow example for analytics pipeline orchestration."""

try:
    from prefect import flow, task
except Exception:
    def task(fn): return fn
    def flow(fn): return fn


@task
def ingest_raw():
    return {"rows": 100}


@task
def validate_clean(payload):
    assert payload["rows"] > 0
    return payload


@task
def build_marts(payload):
    return {"mart_rows": payload["rows"]}


@flow
def raw_to_mart_flow():
    raw = ingest_raw()
    clean = validate_clean(raw)
    return build_marts(clean)
