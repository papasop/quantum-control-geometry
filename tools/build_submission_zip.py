#!/usr/bin/env python3
"""Build the standalone manuscript submission ZIP.

The ZIP is assembled from an explicit allowlist of tracked repository files. It
copies the exact-root ordering certificate byte-for-byte into ``data/`` so that
the bundled Figure 2 generator can re-check interval/order/gap semantics without
depending on the rest of the repository checkout.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "fig2.png",
    "fig_results.pdf",
}
FORBIDDEN_TEXT = ("0.996992", "fig2.png", "fig_results.pdf")
ALLOWLIST = {
    "main.tex": ROOT / "paper" / "main.tex",
    "sec_front.tex": ROOT / "paper" / "sec_front.tex",
    "sec_mid.tex": ROOT / "paper" / "sec_mid.tex",
    "sec_back.tex": ROOT / "paper" / "sec_back.tex",
    "fig1.png": ROOT / "paper" / "fig1.png",
    "fig2_exact_root.png": ROOT / "paper" / "fig2_exact_root.png",
    "manuscript.pdf": ROOT / "paper" / "manuscript.pdf",
    "SUBMISSION_README.md": ROOT / "paper" / "SUBMISSION_README.md",
    "scripts/generate_fig2_exact_root.py": ROOT
    / "paper"
    / "scripts"
    / "generate_fig2_exact_root.py",
    "data/exact_root_ordering_certificate.json": ROOT
    / "results"
    / "exact_root_ordering"
    / "exact_root_ordering_certificate.json",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def assert_tracked(source: Path) -> None:
    relative = source.relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"allowlisted source is not git-tracked: {relative}")


def assert_safe_zip_path(path: str) -> None:
    parts = Path(path).parts
    if any(part in FORBIDDEN_NAMES for part in parts):
        raise SystemExit(f"forbidden path in submission ZIP: {path}")
    if path.startswith("/") or ".." in parts:
        raise SystemExit(f"unsafe path in submission ZIP: {path}")
    if path.endswith((".aux", ".log", ".out", ".toc", ".synctex.gz")):
        raise SystemExit(f"build artifact not allowed in submission ZIP: {path}")


def assert_no_forbidden_payload(path: str, data: bytes) -> None:
    if path.endswith((".tex", ".md", ".txt", ".py", ".json")):
        text = data.decode("utf-8")
        for needle in FORBIDDEN_TEXT:
            if needle in text:
                raise SystemExit(f"forbidden text {needle!r} found in {path}")


def build_payload() -> dict[str, bytes]:
    payload: dict[str, bytes] = {}
    certificate_source = ALLOWLIST["data/exact_root_ordering_certificate.json"]
    canonical_certificate = (
        ROOT / "results" / "exact_root_ordering" / "exact_root_ordering_certificate.json"
    )
    if certificate_source.read_bytes() != canonical_certificate.read_bytes():
        raise SystemExit("bundled data certificate source does not match canonical certificate")

    for zip_path, source in sorted(ALLOWLIST.items()):
        assert_safe_zip_path(zip_path)
        assert_tracked(source)
        data = source.read_bytes()
        assert_no_forbidden_payload(zip_path, data)
        payload[zip_path] = data

    manifest_lines = []
    for zip_path in sorted(payload):
        manifest_lines.append(f"{sha256_bytes(payload[zip_path])}  {zip_path}\n")
    payload["SHA256SUMS.txt"] = "".join(manifest_lines).encode("utf-8")
    return dict(sorted(payload.items()))


def verify_zip(zip_path: Path, expected_payload: dict[str, bytes]) -> None:
    with zipfile.ZipFile(zip_path, "r") as archive:
        names = archive.namelist()
        if names != sorted(expected_payload):
            raise SystemExit("ZIP entries are not exactly the sorted submission payload")
        for name in names:
            assert_safe_zip_path(name)
            data = archive.read(name)
            if data != expected_payload[name]:
                raise SystemExit(f"ZIP payload mismatch for {name}")
            assert_no_forbidden_payload(name, data)

        with tempfile.TemporaryDirectory() as temp_dir:
            archive.extractall(temp_dir)
            result = subprocess.run(
                ["sha256sum", "-c", "SHA256SUMS.txt"],
                cwd=temp_dir,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if result.returncode != 0:
                sys.stdout.write(result.stdout)
                raise SystemExit("submission manifest check failed after ZIP extraction")


def write_zip(zip_path: Path) -> None:
    payload = build_payload()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for name, data in payload.items():
            info = zipfile.ZipInfo(name)
            info.date_time = (2026, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)

    verify_zip(zip_path, payload)
    print(f"submission ZIP: {zip_path}")
    print(f"entries: {len(payload)}")
    print(f"ZIP SHA-256: {sha256_file(zip_path)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_zip(args.output)


if __name__ == "__main__":
    main()
