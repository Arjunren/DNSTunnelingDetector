# Dataset handling

The official [CIC-Bell-DNS-EXF-2021 dataset](https://www.unb.ca/cic/datasets/dns-exf-2021.html) contains research DNS exfiltration traffic. Use only according to its source terms and citation requirements. This repository does not download, bundle, or redistribute the dataset. Convert authorized source traces or local DNS logs into the normalized JSONL event format documented below; the preparation script computes metadata windows without issuing DNS queries. Training CSVs require the numeric fields in `src/dns_tunneling_detector/features.py`, `group_id`, and reviewed binary `label` (0 benign, 1 tunneling-like). Related traffic from the same collection campaign must share a group. Raw and processed data are Git ignored.

`scripts/prepare_dns.py` accepts local JSONL events with these fields: timezone-aware ISO 8601 `timestamp`, ASCII/IDNA `qname`, trusted `base_domain`, `qtype` (`A`, `AAAA`, `CNAME`, `TXT`, `MX`, `NS`, `SRV`, `OTHER`), `rcode` (`NOERROR`, `NXDOMAIN`, `SERVFAIL`, `REFUSED`, `OTHER`), `sensor_group`, and integer `reviewed_label` 0 or 1. `base_domain` must be supplied by a trusted upstream parser or dataset annotation; the script verifies it is a suffix and never guesses an effective top-level domain. Every event in one window must have the same reviewed label. No DNS resolution occurs.

Example inert event:

```json
{"timestamp":"2026-01-01T12:00:00Z","qname":"abc.example.test","base_domain":"example.test","qtype":"TXT","rcode":"NXDOMAIN","sensor_group":"reviewed-campaign-001","reviewed_label":1}
```

Run `python scripts/prepare_dns.py --input data/raw/dns.jsonl --output data/processed/training.csv`. The script writes 5-minute windows by `sensor_group` and `base_domain`; identifiers are mapped to numeric group IDs, and raw query names are omitted from output. `sensor_group` should join related traffic across domains to keep campaigns in one train/validation/test partition. The source file is capped at 128 MiB; prepare larger research sources in authorized chunks, then check group consistency before combining. Keep both raw and aggregate data in protected storage.
