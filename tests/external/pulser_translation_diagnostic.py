#!/usr/bin/env python3
"""Compatibility wrapper for the Pulser report validator."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from validate_pulser_translation_report import (  # noqa: E402
    EXPECTED_ORDER,
    EXPECTED_STATUS,
    REPORT,
    load_report,
    main,
    validate_report,
)


if __name__ == "__main__":
    sys.exit(main())
