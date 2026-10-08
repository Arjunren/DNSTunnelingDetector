import csv
import json
from pathlib import Path

import pytest

from scripts.prepare_dns import normalize, prepare


def test_dns_window_features(tmp_path: Path) -> None:
    events = [
        {
            "timestamp": "2026-01-01T12:00:00Z",
            "qname": "abc.example.test",
            "base_domain": "example.test",
            "qtype": "TXT",
            "rcode": "NXDOMAIN",
            "sensor_group": "private-campaign",
            "reviewed_label": 1,
        },
        {
            "timestamp": "2026-01-01T12:00:05Z",
            "qname": "def.example.test",
            "base_domain": "example.test",
            "qtype": "A",
            "rcode": "NOERROR",
            "sensor_group": "private-campaign",
            "reviewed_label": 1,
        },
    ]
    source = tmp_path / "dns.jsonl"
    source.write_text("\n".join(json.dumps(item) for item in events) + "\n", encoding="utf-8")
    output = tmp_path / "training.csv"
    assert prepare(source, output) == 1
    with output.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["query_count"] == "2"
    assert row["txt_query_ratio"] == "0.5"
    assert row["nxdomain_ratio"] == "0.5"
    assert "private-campaign" not in output.read_text(encoding="utf-8")


def test_rejects_domain_outside_base_and_naive_time() -> None:
    record = {
        "timestamp": "2026-01-01T12:00:00Z",
        "qname": "example.attacker.test",
        "base_domain": "example.test",
        "qtype": "A",
        "rcode": "NOERROR",
        "sensor_group": "test",
        "reviewed_label": 0,
    }
    with pytest.raises(ValueError):
        normalize(record)
    record["qname"] = "example.test"
    record["timestamp"] = "2026-01-01T12:00:00"
    with pytest.raises(ValueError):
        normalize(record)
