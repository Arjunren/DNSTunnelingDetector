from pathlib import Path

import pytest

from dns_tunneling_detector.artifact import Model, load_model, save_model
from dns_tunneling_detector.features import FEATURE_NAMES, Observation


@pytest.fixture
def observation() -> Observation:
    return Observation.model_validate(
        {
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
    )


@pytest.fixture
def model(tmp_path: Path) -> Model:
    size = len(FEATURE_NAMES)
    payload = {
        "features": list(FEATURE_NAMES),
        "means": [0.0] * size,
        "scales": [1.0] * size,
        "coefficients": [0.001] * size,
        "intercept": -1.0,
        "threshold": 0.5,
        "version": "test-1",
    }
    path = tmp_path / "model.json"
    save_model(path, payload)
    return load_model(path)
