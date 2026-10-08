"""Aggregate local DNS JSONL metadata without performing network requests."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dns_tunneling_detector.features import RAW_FIELDS, Observation

MAX_FILE_BYTES = 128 * 1024 * 1024
MAX_LINE_BYTES = 4096
MAX_EVENTS = 1_000_000
LABEL_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _domain(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a domain string")
    domain = value.removesuffix(".").lower()
    labels = domain.split(".")
    if not 1 <= len(domain) <= 253 or any(
        not 1 <= len(label) <= 63 or not LABEL_RE.fullmatch(label) for label in labels
    ):
        raise ValueError(f"Invalid {name}")
    return domain


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError("Invalid timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")
    return parsed.astimezone(UTC)


def normalize(record: dict[str, Any]) -> dict[str, Any]:
    qname = _domain(record.get("qname"), "qname")
    base = _domain(record.get("base_domain"), "base_domain")
    if len(base.split(".")) < 2 or not (qname == base or qname.endswith("." + base)):
        raise ValueError("qname must be within base_domain")
    qtype = record.get("qtype")
    rcode = record.get("rcode")
    if qtype not in ("A", "AAAA", "CNAME", "TXT", "MX", "NS", "SRV", "OTHER"):
        raise ValueError("Unsupported qtype")
    if rcode not in ("NOERROR", "NXDOMAIN", "SERVFAIL", "REFUSED", "OTHER"):
        raise ValueError("Unsupported rcode")
    group = record.get("sensor_group")
    if not isinstance(group, str) or not 1 <= len(group) <= 128:
        raise ValueError("Invalid sensor_group")
    label = record.get("reviewed_label")
    if type(label) is not int or label not in (0, 1):
        raise ValueError("reviewed_label must be 0 or 1")
    return {
        "timestamp": _timestamp(record.get("timestamp")),
        "qname": qname,
        "base": base,
        "subdomain": qname[: -len(base) - 1] if qname != base else "",
        "qtype": qtype,
        "rcode": rcode,
        "group": group,
        "label": label,
    }


def _entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    return -sum((count / len(value)) * math.log2(count / len(value)) for count in counts.values())


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def prepare(source: Path, output: Path, window_seconds: int = 300) -> int:
    if source.resolve() == output.resolve():
        raise ValueError("Input and output paths must differ")
    if not 60 <= window_seconds <= 86400:
        raise ValueError("window_seconds must be between 60 and 86400")
    if source.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Source file is too large")
    windows: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    with source.open("rb") as handle:
        for number, raw in enumerate(handle, 1):
            if number > MAX_EVENTS or len(raw) > MAX_LINE_BYTES:
                raise ValueError("Source exceeds event or line limit")
            try:
                record = json.loads(raw)
                if not isinstance(record, dict):
                    raise ValueError("DNS event must be an object")
                event = normalize(record)
            except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"Invalid DNS event at line {number}") from exc
            bucket = math.floor(event["timestamp"].timestamp() / window_seconds)
            windows[(event["group"], event["base"], bucket)].append(event)
    if not windows:
        raise ValueError("No DNS events")
    group_ids = {name: index for index, name in enumerate(sorted({key[0] for key in windows}))}
    rows: list[dict[str, Any]] = []
    for (group, _base, _bucket), events in sorted(windows.items()):
        labels = {event["label"] for event in events}
        if len(labels) != 1:
            raise ValueError("Every event in a window needs the same reviewed_label")
        count = len(events)
        subs = [event["subdomain"] for event in events]
        fields = {
            "query_count": count,
            "mean_query_length": _mean([float(len(event["qname"])) for event in events]),
            "mean_subdomain_length": _mean([float(len(value)) for value in subs]),
            "mean_subdomain_entropy": _mean([_entropy(value) for value in subs]),
            "mean_unique_character_ratio": _mean(
                [len(set(value)) / len(value) if value else 0.0 for value in subs]
            ),
            "txt_query_ratio": sum(event["qtype"] == "TXT" for event in events) / count,
            "nxdomain_ratio": sum(event["rcode"] == "NXDOMAIN" for event in events) / count,
            "unique_subdomain_ratio": len(set(subs)) / count,
            "queries_per_minute": count / (window_seconds / 60),
            "max_label_length": max(
                len(label) for event in events for label in event["qname"].split(".")
            ),
            "punycode_ratio": sum(
                any(label.startswith("xn--") for label in event["qname"].split("."))
                for event in events
            )
            / count,
            "window_seconds": window_seconds,
        }
        Observation.model_validate(fields)
        rows.append({**fields, "group_id": group_ids[group], "label": labels.pop()})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*RAW_FIELDS, "group_id", "label"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--window-seconds", type=int, default=300)
    args = parser.parse_args()
    print(f"wrote {prepare(args.input, args.output, args.window_seconds)} windows")


if __name__ == "__main__":
    main()
