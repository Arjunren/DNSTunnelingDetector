"""Validated domain telemetry and deterministic feature engineering."""

from __future__ import annotations

import math

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

RAW_FIELDS = (
    "query_count",
    "mean_query_length",
    "mean_subdomain_length",
    "mean_subdomain_entropy",
    "mean_unique_character_ratio",
    "txt_query_ratio",
    "nxdomain_ratio",
    "unique_subdomain_ratio",
    "queries_per_minute",
    "max_label_length",
    "punycode_ratio",
    "window_seconds",
)
FEATURE_NAMES = (
    "query_count",
    "mean_query_length",
    "mean_subdomain_length",
    "mean_subdomain_entropy",
    "mean_unique_character_ratio",
    "txt_query_ratio",
    "nxdomain_ratio",
    "unique_subdomain_ratio",
    "queries_per_minute",
    "max_label_length",
    "punycode_ratio",
    "window_seconds",
    "query_volume_log",
    "length_x_entropy",
    "nxdomain_volume",
)


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_count: int = Field(ge=1, le=1000000)
    mean_query_length: float = Field(ge=1, le=253)
    mean_subdomain_length: float = Field(ge=0, le=253)
    mean_subdomain_entropy: float = Field(ge=0, le=8)
    mean_unique_character_ratio: float = Field(ge=0, le=1)
    txt_query_ratio: float = Field(ge=0, le=1)
    nxdomain_ratio: float = Field(ge=0, le=1)
    unique_subdomain_ratio: float = Field(ge=0, le=1)
    queries_per_minute: float = Field(ge=0, le=1000000)
    max_label_length: int = Field(ge=1, le=63)
    punycode_ratio: float = Field(ge=0, le=1)
    window_seconds: float = Field(ge=60, le=86400)

    @field_validator(
        "mean_query_length",
        "mean_subdomain_length",
        "mean_subdomain_entropy",
        "mean_unique_character_ratio",
        "txt_query_ratio",
        "nxdomain_ratio",
        "unique_subdomain_ratio",
        "queries_per_minute",
        "punycode_ratio",
        "window_seconds",
    )
    @classmethod
    def finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("Feature must be finite")
        return value


def extract_features(observation: Observation) -> np.ndarray:
    values = observation.model_dump()
    result = [float(values[name]) for name in RAW_FIELDS]
    result.append(float(math.log1p(values["query_count"])))  # query_volume_log
    result.append(
        float(values["mean_subdomain_length"] * values["mean_subdomain_entropy"])
    )  # length_x_entropy
    result.append(float(values["nxdomain_ratio"] * values["query_count"]))  # nxdomain_volume
    return np.asarray(result, dtype=np.float64)


def feature_matrix(observations: list[Observation]) -> np.ndarray:
    if not observations:
        raise ValueError("At least one observation is required")
    return np.vstack([extract_features(item) for item in observations])
