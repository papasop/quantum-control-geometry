#!/usr/bin/env python3
"""Validate the committed Pulser translation report."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC = ROOT / "tests/external/pulser_translation_diagnostic.py"


def main() -> int:
    spec = importlib.util.spec_from_file_location(
        "pulser_translation_diagnostic", DIAGNOSTIC
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.load_report()
    module.validate_report(report)
    print(f"Pulser translation report: {report['scientific_status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
