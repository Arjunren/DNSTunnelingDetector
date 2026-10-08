"""Deterministic synthetic telemetry for smoke tests only."""

import argparse
import csv
import random
from pathlib import Path

from dns_tunneling_detector.features import RAW_FIELDS

BENIGN = {
    "query_count": 20,
    "mean_query_length": 24,
    "mean_subdomain_length": 5,
    "mean_subdomain_entropy": 1.8,
    "mean_unique_character_ratio": 0.6,
    "txt_query_ratio": 0.05,
    "nxdomain_ratio": 0.02,
    "unique_subdomain_ratio": 0.1,
    "queries_per_minute": 4,
    "max_label_length": 12,
    "punycode_ratio": 0,
    "window_seconds": 300,
}
POSITIVE = {
    "query_count": 300,
    "mean_query_length": 100,
    "mean_subdomain_length": 70,
    "mean_subdomain_entropy": 4.5,
    "mean_unique_character_ratio": 0.9,
    "txt_query_ratio": 0.6,
    "nxdomain_ratio": 0.4,
    "unique_subdomain_ratio": 0.95,
    "queries_per_minute": 60,
    "max_label_length": 55,
    "punycode_ratio": 0.1,
    "window_seconds": 300,
}
BOUNDS = {
    "query_count": (1, 1000000, "int"),
    "mean_query_length": (1, 253, "float"),
    "mean_subdomain_length": (0, 240, "float"),
    "mean_subdomain_entropy": (0, 8, "float"),
    "mean_unique_character_ratio": (0, 1, "float"),
    "txt_query_ratio": (0, 1, "float"),
    "nxdomain_ratio": (0, 1, "float"),
    "unique_subdomain_ratio": (0, 1, "float"),
    "queries_per_minute": (0, 1000000, "float"),
    "max_label_length": (1, 63, "int"),
    "punycode_ratio": (0, 1, "float"),
    "window_seconds": (60, 86400, "float"),
}


def generate(output: Path) -> None:
    rng = random.Random(42)  # noqa: S311  # nosec B311
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*RAW_FIELDS, "group_id", "label"])
        writer.writeheader()
        for label, baseline in ((0, BENIGN), (1, POSITIVE)):
            for index in range(80):
                row = {}
                for name, base in baseline.items():
                    lower, upper, kind = BOUNDS[name]
                    if kind == "int":
                        jitter = rng.randint(-2, 2)
                        row[name] = int(max(lower, min(upper, base + jitter)))
                    else:
                        jitter = rng.uniform(-0.05, 0.05) * max(abs(base), 1)
                        row[name] = float(max(lower, min(upper, base + jitter)))
                writer.writerow({**row, "group_id": f"{label}-{index}", "label": label})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/processed/synthetic.csv"))
    args = parser.parse_args()
    generate(args.output)
    print(args.output)


if __name__ == "__main__":
    main()
