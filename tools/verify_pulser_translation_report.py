#!/usr/bin/env python3
"""Validate the committed Pulser translation report."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from validate_pulser_translation_report import load_report, validate_report  # noqa: E402


def main() -> int:
    report = load_report()
    validate_report(report)
    print(f"Pulser translation report: {report['scientific_status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
