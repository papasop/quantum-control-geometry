#!/usr/bin/env python3
"""
Clean-environment Colab reproduction for Quantum Control Geometry v0.3.1.

Colab usage
-----------
1. Upload this file to /content.
2. Run:

       %run /content/external_reproduce_v0_3_1.py

No PASQAL account or password is required.

Scope
-----
This verifies and recomputes the certificates for the frozen serialized
two-atom model. It is not PASQAL Cloud or QPU evidence.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence


REPOSITORY_URL = "https://github.com/papasop/quantum-control-geometry.git"
FROZEN_TAG = "v0.3.1"
EXPECTED_COMMIT = "284974c9f6b952f4e114c8c5bdc9c2c299c4065c"

# Set this to False only if you want the fast bundled-artifact checks without
# rerunning the complete formal certificate.
RUN_COMPLETE_FORMAL_RECOMPUTATION = True

BASE_DIRECTORY = Path("/content") if Path("/content").is_dir() else Path.cwd()
WORK_DIRECTORY = BASE_DIRECTORY / "quantum-control-geometry-v0.3.1-external"


def banner(message: str) -> None:
    print("\n" + "=" * 100, flush=True)
    print(message, flush=True)
    print("=" * 100, flush=True)


def run(arguments: Sequence[str], *, cwd: Path | None = None) -> None:
    printable = " ".join(str(value) for value in arguments)
    print(f"\n$ {printable}", flush=True)
    started = time.time()
    environment = dict(os.environ)
    environment["PYTHONUNBUFFERED"] = "1"
    subprocess.run(
        [str(value) for value in arguments],
        cwd=cwd,
        env=environment,
        check=True,
        text=True,
    )
    print(f"[completed in {time.time() - started:.1f} s]", flush=True)


def checked_output(arguments: Sequence[str], *, cwd: Path) -> str:
    return subprocess.check_output(
        [str(value) for value in arguments],
        cwd=cwd,
        text=True,
    ).strip()


def main() -> None:
    total_started = time.time()

    banner("QUANTUM CONTROL GEOMETRY v0.3.1 - CLEAN-ENVIRONMENT REPRODUCTION")
    print("No PASQAL account or password is required.", flush=True)
    print(f"Working directory: {WORK_DIRECTORY}", flush=True)

    banner("STAGE 0 - CHECK OUT THE FROZEN SCIENTIFIC VERSION")

    if WORK_DIRECTORY.exists():
        print(f"Removing previous run directory: {WORK_DIRECTORY}", flush=True)
        shutil.rmtree(WORK_DIRECTORY)

    run(
        [
            "git",
            "clone",
            "--branch",
            FROZEN_TAG,
            "--depth",
            "1",
            REPOSITORY_URL,
            str(WORK_DIRECTORY),
        ]
    )

    actual_commit = checked_output(
        ["git", "rev-parse", "HEAD"],
        cwd=WORK_DIRECTORY,
    )

    print(f"\nFrozen tag:      {FROZEN_TAG}")
    print(f"Expected commit: {EXPECTED_COMMIT}")
    print(f"Actual commit:   {actual_commit}")

    if actual_commit != EXPECTED_COMMIT:
        raise RuntimeError(
            "Frozen commit mismatch: the checked-out tag does not resolve "
            "to the predeclared v0.3.1 commit."
        )

    print("Frozen commit match: PASS", flush=True)

    banner("STAGE 1 - INSTALL THE FROZEN DEPENDENCIES")
    run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            "requirements.txt",
        ],
        cwd=WORK_DIRECTORY,
    )

    banner("STAGE 2 - VERIFY THE BUNDLED REFERENCE ARTIFACTS")

    run(
        [sys.executable, "tools/verify_reference_results.py"],
        cwd=WORK_DIRECTORY,
    )
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-v",
        ],
        cwd=WORK_DIRECTORY,
    )
    run(
        ["sha256sum", "-c", "SHA256SUMS.txt"],
        cwd=WORK_DIRECTORY,
    )

    if RUN_COMPLETE_FORMAL_RECOMPUTATION:
        banner(
            "STAGE 3 - RERUN THE COMPLETE FORMAL v1.3 CERTIFICATE TWICE"
        )
        print(
            "This is the long stage and may take several minutes.",
            flush=True,
        )
        run(
            [
                sys.executable,
                "scripts/standalone/"
                "pasqal_L4_reproducible_certificate_v1_3_colab.py",
            ],
            cwd=WORK_DIRECTORY,
        )
        formal_status = "PASS"
    else:
        formal_status = "SKIPPED_BY_LOCAL_CONFIGURATION"

    banner("CLEAN-ENVIRONMENT REPRODUCTION COMPLETED")

    print(f"Frozen tag:                         {FROZEN_TAG}")
    print(f"Frozen commit:                      {actual_commit}")
    print("Bundled artifact verification:      PASS")
    print("Regression tests:                   PASS")
    print("Repository SHA-256 snapshot:        PASS")
    print(f"Complete formal v1.3 recomputation: {formal_status}")

    if RUN_COMPLETE_FORMAL_RECOMPUTATION:
        print(
            "Expected exact-root result:         "
            "Krawczyk inclusions 12/12"
        )
        print(
            "Expected mechanism result:          "
            "order-30 exact-root 52/66, zero reversals"
        )
        print(
            "Expected theorem-level result:      "
            "exact-root direct ordering 66/66"
        )
        print(
            "Expected reproducibility result:    "
            "two-run byte identity PASS"
        )

    print(
        f"\nTotal elapsed time: {time.time() - total_started:.1f} s",
        flush=True,
    )
    print(
        "Scope: serialized two-atom model; not PASQAL QPU evidence.",
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        banner("CLEAN-ENVIRONMENT REPRODUCTION: FAIL")
        print(f"{type(error).__name__}: {error}", flush=True)
        raise
