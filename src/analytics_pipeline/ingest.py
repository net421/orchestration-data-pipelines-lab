from pathlib import Path
import pandas as pd

from .retry import retry


@retry(attempts=3, base_delay_seconds=0.05, retry_on=(OSError,))
def read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV with bounded retries for transient filesystem failures."""
    return pd.read_csv(path)


def ingest_sources(input_dir: Path) -> dict[str, pd.DataFrame]:
    required = {
        "orders": input_dir / "erp_order_lines.csv",
        "shipments": input_dir / "tms_shipments.csv",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required source files: {missing}")
    return {name: read_csv(path) for name, path in required.items()}
