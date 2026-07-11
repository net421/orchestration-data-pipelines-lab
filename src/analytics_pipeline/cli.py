from __future__ import annotations

import argparse
import json

from .config import PipelineConfig
from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the supply-chain analytics pipeline.")
    parser.add_argument("--input-dir", default="data/raw")
    parser.add_argument("--output-dir", default="data/published")
    parser.add_argument("--run-dir", default="runs")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    result = run_pipeline(
        PipelineConfig.from_strings(args.input_dir, args.output_dir, args.run_dir),
        run_id=args.run_id,
    )
    print(json.dumps(result.__dict__, indent=2))


if __name__ == "__main__":
    main()
