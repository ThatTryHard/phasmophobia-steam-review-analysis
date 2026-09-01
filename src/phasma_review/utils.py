"""Small deterministic utilities shared across the pipeline."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

RANDOM_SEED = 20260813


def sha256_file(path: Path) -> str:
    """Hash the exact bytes of an immutable source or binary artifact."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text_file(path: Path) -> str:
    """Hash UTF-8 text after normalizing platform-specific line endings.

    Generated CSV files can be CRLF in a Windows working tree and LF after
    Git checks them out on Linux. Normalizing newlines preserves an integrity
    check on the text content without making the manifest operating-system
    dependent.
    """

    content = path.read_text(encoding="utf-8")
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""

    if total <= 0:
        return (math.nan, math.nan)
    proportion = successes / total
    denominator = 1 + z**2 / total
    center = (proportion + z**2 / (2 * total)) / denominator
    half_width = (
        z
        * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2))
        / denominator
    )
    return center - half_width, center + half_width


def percentile_interval(
    values: list[float] | np.ndarray,
    lower: float = 2.5,
    upper: float = 97.5,
) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return (math.nan, math.nan)
    return tuple(np.percentile(array, [lower, upper]).tolist())


def largest_remainder_allocation(
    group_sizes: dict[str, int],
    total: int,
) -> dict[str, int]:
    """Allocate an exact total proportionally across named groups."""

    population = sum(group_sizes.values())
    if total < 0 or total > population:
        raise ValueError("Allocation total must be within the population size.")
    if population == 0:
        return {key: 0 for key in group_sizes}

    exact = {key: total * size / population for key, size in group_sizes.items()}
    allocated = {key: math.floor(value) for key, value in exact.items()}
    remaining = total - sum(allocated.values())
    order = sorted(
        group_sizes,
        key=lambda key: (exact[key] - allocated[key], group_sizes[key], key),
        reverse=True,
    )
    for key in order[:remaining]:
        allocated[key] += 1
    return allocated
