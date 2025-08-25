"""
Creative-related Pydantic models.
Extracted from schemas.py to reduce file size and improve maintainability.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CreativeGroup(BaseModel):
    group_id: str
    name: str
    description: str | None = None
    creatives: list["Creative"]
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Creative(BaseModel):
    creative_id: str
    name: str
    description: str | None = None
    format_id: str
    assets: list[dict[str, Any]]  # Asset data
    status: Literal["pending", "approved", "rejected", "active", "paused"] = "pending"
    performance_metrics: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CreativeAdaptation(BaseModel):
    adaptation_id: str
    original_creative_id: str
    adapted_assets: list[dict[str, Any]]
    adaptation_type: str  # e.g., "resize", "reformat", "optimize"
    status: Literal["pending", "approved", "rejected"] = "pending"
    approval_notes: str | None = None
    created_at: datetime | None = None


class CreativeStatus(BaseModel):
    creative_id: str
    status: str
    message: str | None = None
    details: dict[str, Any] | None = None
