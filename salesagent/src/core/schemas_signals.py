"""
AEE signals and capabilities Pydantic models.
Extracted from schemas.py to reduce file size and improve maintainability.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class GetTargetingCapabilitiesRequest(BaseModel):
    principal_id: str
    adapter_type: str | None = None
    include_advanced: bool = True


class TargetingDimensionInfo(BaseModel):
    dimension: str
    display_name: str
    description: str | None = None
    type: str
    required: bool = False
    options: list[str] | None = None
    min_value: float | None = None
    max_value: float | None = None
    unit: str | None = None


class ChannelTargetingCapabilities(BaseModel):
    channel: str
    dimensions: list[TargetingDimensionInfo]


class GetTargetingCapabilitiesResponse(BaseModel):
    principal_id: str
    channels: list[ChannelTargetingCapabilities]


class CheckAEERequirementsRequest(BaseModel):
    media_buy_id: str
    targeting_overlay: dict[str, Any] | None = None
    creative_assets: list[dict[str, Any]] | None = None


class CheckAEERequirementsResponse(BaseModel):
    media_buy_id: str
    requirements_met: bool
    missing_requirements: list[str]
    recommendations: list[str]
    compliance_score: float


class Signal(BaseModel):
    signal_id: str
    signal_type: str
    signal_value: Any
    confidence_score: float | None = None
    source: str
    timestamp: datetime
    metadata: dict[str, Any] | None = None


class GetSignalsRequest(BaseModel):
    principal_id: str
    signal_types: list[str] | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    limit: int | None = None


class GetSignalsResponse(BaseModel):
    principal_id: str
    signals: list[Signal]
    total_count: int
    has_more: bool
