from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .runner import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the documentation pipeline (Structurizr + PDF tools)",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to docs-pipeline YAML configuration file",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"[ERROR] Config file not found: {config_path}")
        sys.exit(1)

    success = run_pipeline(config_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


