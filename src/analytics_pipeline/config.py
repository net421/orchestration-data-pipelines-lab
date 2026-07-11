from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    input_dir: Path
    output_dir: Path
    run_dir: Path

    @classmethod
    def from_strings(cls, input_dir: str, output_dir: str, run_dir: str) -> "PipelineConfig":
        return cls(Path(input_dir), Path(output_dir), Path(run_dir))
