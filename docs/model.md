# Model card — DNSTunnelingDetector 1.0.0

| Field | Description |
| --- | --- |
| Purpose | The detector scores DNS query windows for tunneling-like behavior using query shape, subdomain entropy and uniqueness, request rate, TXT usage, and NXDOMAIN frequency. |
| Model type | Standardized numeric features and class-weighted logistic regression. |
| Training dataset | Operator-provided, labeled normalized CSV derived from CIC-Bell-DNS-EXF-2021; no data bundled. |
| Feature set | query_count, mean_query_length, mean_subdomain_length, mean_subdomain_entropy, mean_unique_character_ratio, txt_query_ratio, nxdomain_ratio, unique_subdomain_ratio, queries_per_minute, max_label_length, punycode_ratio, window_seconds, query_volume_log, length_x_entropy, nxdomain_volume. |
| Evaluation metrics | Precision, recall, F1, ROC-AUC, PR-AUC, FPR, FNR, confusion matrix, and class support in per-training metadata. No default score claimed. |
| Known limitations | High-entropy CDNs, telemetry, and long legitimate DNS names can resemble tunnels; encrypted DNS and low-rate channels can evade metadata-only detection. |
| Bias considerations | Source coverage and labeling can differ across entities, time, and environments; inspect group-level error rates. |
| Security considerations | Validate telemetry, protect datasets against poisoning, and review artifact provenance. |
| Intended use | Analyst decision support and research baseline. |
| Out-of-scope use | Sole high-impact control or claim of confirmed maliciousness. |
| Version | JSON format `dns-tunneling-detector-logreg-v1`; model version supplied at training. |

Confidence is a model estimate, not certainty. Local feature contributions describe the linear score and are not causal proof.
