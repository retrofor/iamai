from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from iamai import Runtime


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the iamai persona roleplay example")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).with_name("config.terminal.toml")),
        help="Path to the example TOML config file",
    )
    args = parser.parse_args()
    runtime = Runtime.from_config_file(args.config)
    asyncio.run(runtime.serve())


if __name__ == "__main__":
    main()
