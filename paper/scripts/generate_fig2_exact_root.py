#!/usr/bin/env python3
"""Generate Figure 2 from the frozen exact-root ordering certificate.

The interval, order, disjointness, and minimum-gap semantics are derived from
the committed exact-root certificate and checked before plotting. PNG pixel-byte
identity additionally depends on the pinned Matplotlib/font environment and is
not part of the mathematical certificate.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, localcontext
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CERTIFICATE = (
    REPO_ROOT
    / "results"
    / "exact_root_ordering"
    / "exact_root_ordering_certificate.json"
)
DEFAULT_OUTPUT = REPO_ROOT / "paper" / "fig2_exact_root.png"
EXPECTED_ORDER = [
    "pv07",
    "pv01",
    "pv10",
    "pv05",
    "pv04",
    "pv02",
    "pv08",
    "pv11",
    "pv09",
    "pv03",
    "pv12",
    "pv06",
]
EXPECTED_MIN_GAP_PAIR = ("pv08", "pv11")
INTERVAL_RE = re.compile(r"^\[([^\]]+?) \+/- [^\]]+\]$")


@dataclass(frozen=True)
class PathInterval:
    path: str
    lower: Decimal
    upper: Decimal

    @property
    def mid(self) -> Decimal:
        return (self.lower + self.upper) / Decimal(2)


def parse_arb_endpoint(text: str) -> Decimal:
    """Parse a full-precision Arb endpoint string such as ``[1.23 +/- 1e-60]``."""
    match = INTERVAL_RE.match(text)
    if not match:
        raise ValueError(f"unexpected Arb endpoint format: {text!r}")
    with localcontext() as ctx:
        ctx.prec = 90
        return Decimal(match.group(1))


def load_direct_intervals(certificate_path: Path = DEFAULT_CERTIFICATE) -> list[PathInterval]:
    obj = json.loads(certificate_path.read_text(encoding="utf-8"))
    rows = obj["path_rows"]
    intervals = []
    for row in rows:
        direct = row["direct_mean_interval"]
        intervals.append(
            PathInterval(
                path=row["path"],
                lower=parse_arb_endpoint(direct["lower"]),
                upper=parse_arb_endpoint(direct["upper"]),
            )
        )
    return intervals


def truncate_decimal_sigfig(value: Decimal, sigfigs: int = 3) -> Decimal:
    if value <= 0:
        raise ValueError("positive value required")
    exponent = value.adjusted() - sigfigs + 1
    quantum = Decimal(f"1e{exponent}")
    return value.quantize(quantum, rounding=ROUND_DOWN)


def format_decimal_scientific(value: Decimal, sigfigs: int = 3) -> str:
    truncated = truncate_decimal_sigfig(value, sigfigs=sigfigs)
    exponent = truncated.adjusted()
    mantissa = truncated.scaleb(-exponent)
    places = max(sigfigs - 1, 0)
    return f"{mantissa:.{places}f}e{exponent}"


def compute_figure_data(
    certificate_path: Path = DEFAULT_CERTIFICATE,
) -> dict[str, object]:
    intervals = load_direct_intervals(certificate_path)
    paths = [item.path for item in intervals]
    if len(intervals) != 12 or len(set(paths)) != 12:
        raise AssertionError(f"expected 12 distinct paths, got {paths}")

    ordered = sorted(intervals, key=lambda item: item.mid)
    order = [item.path for item in ordered]
    if order != EXPECTED_ORDER:
        raise AssertionError(f"unexpected exact-root order: {order}")

    disjoint_pairs = 0
    for i, left in enumerate(ordered):
        for right in ordered[i + 1 :]:
            if not left.upper < right.lower:
                raise AssertionError(
                    f"overlapping direct intervals: {left.path} and {right.path}"
                )
            disjoint_pairs += 1
    if disjoint_pairs != 66:
        raise AssertionError(f"expected 66 disjoint pairs, got {disjoint_pairs}")

    adjacent_gaps = []
    for left, right in zip(ordered, ordered[1:]):
        adjacent_gaps.append(
            {
                "left": left.path,
                "right": right.path,
                "gap": right.lower - left.upper,
            }
        )
    minimum_gap = min(adjacent_gaps, key=lambda item: item["gap"])
    minimum_pair = (str(minimum_gap["left"]), str(minimum_gap["right"]))
    if minimum_pair != EXPECTED_MIN_GAP_PAIR:
        raise AssertionError(f"unexpected minimum-gap pair: {minimum_pair}")

    display_gap = format_decimal_scientific(minimum_gap["gap"])
    if display_gap != "2.50e-5":
        raise AssertionError(f"unexpected displayed minimum gap: {display_gap}")

    return {
        "certificate_path": certificate_path,
        "intervals": ordered,
        "order": order,
        "disjoint_pairs": disjoint_pairs,
        "minimum_gap_pair": minimum_pair,
        "minimum_gap": minimum_gap["gap"],
        "display_gap": display_gap,
    }


def plot_figure(data: dict[str, object], output_path: Path = DEFAULT_OUTPUT) -> None:
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/qcg-matplotlib")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    intervals = data["intervals"]
    assert isinstance(intervals, list)
    display_gap = str(data["display_gap"])
    min_pair = tuple(data["minimum_gap_pair"])
    mantissa, exponent = display_gap.split("e")
    math_gap = rf"{mantissa}\times10^{{{int(exponent)}}}"

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
        }
    )
    fig, ax = plt.subplots(figsize=(6.8, 4.2), dpi=180)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    for y, item in enumerate(intervals):
        assert isinstance(item, PathInterval)
        lower = float(item.lower)
        upper = float(item.upper)
        mid = float(item.mid)
        color = "#1f77b4"
        linewidth = 1.6
        if item.path in min_pair:
            color = "#b3261e"
            linewidth = 2.2
        ax.hlines(y, lower, upper, color=color, linewidth=linewidth)
        ax.plot(mid, y, "o", color=color, markersize=3.6)

    ax.set_yticks(list(range(len(intervals))))
    ax.set_yticklabels([item.path for item in intervals])
    ax.invert_yaxis()
    ax.set_xlabel("Direct mean finite-error loss interval")
    ax.set_title("Exact-root certified direct Arb intervals")
    ax.grid(axis="x", color="#d9d9d9", linewidth=0.6)
    ax.grid(axis="y", color="#eeeeee", linewidth=0.4)

    left_item = next(item for item in intervals if item.path == min_pair[0])
    right_item = next(item for item in intervals if item.path == min_pair[1])
    x0 = float(left_item.upper)
    x1 = float(right_item.lower)
    y0 = intervals.index(left_item)
    y1 = intervals.index(right_item)
    ax.annotate(
        rf"$\Delta_{{\min}}={math_gap}$",
        xy=((x0 + x1) / 2.0, (y0 + y1) / 2.0),
        xytext=(0.1110, (y0 + y1) / 2.0 + 1.2),
        arrowprops={"arrowstyle": "->", "color": "#b3261e", "linewidth": 0.9},
        color="#7a1b14",
        fontsize=9,
    )

    ax.margins(x=0.04, y=0.08)
    fig.tight_layout()
    fig.savefig(
        output_path,
        dpi=180,
        facecolor="white",
        transparent=False,
        bbox_inches="tight",
        pad_inches=0.06,
    )
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certificate", type=Path, default=DEFAULT_CERTIFICATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    data = compute_figure_data(args.certificate)
    plot_figure(data, args.output)

    print(f"input certificate path: {args.certificate}")
    print(f"number of paths: {len(data['order'])}")
    print(f"disjoint pairs: {data['disjoint_pairs']}/66")
    print(f"computed order: {data['order']}")
    print(f"minimum-gap pair: {data['minimum_gap_pair'][0]} -> {data['minimum_gap_pair'][1]}")
    print(f"full-precision minimum gap: {data['minimum_gap']}")
    print(f"displayed minimum gap: {data['display_gap']}")
    print(f"output path: {args.output}")


if __name__ == "__main__":
    main()
