#!/usr/bin/env python3
"""
Foundational Creative Formats System

This module implements the AdContext Protocol's foundational creative format system,
allowing publishers to extend base formats while maintaining standardization.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FoundationalFormat:
    """Represents a foundational creative format."""

    format_id: str
    name: str
    type: str
    description: str
    is_standard: bool = True
    is_foundational: bool = True
    assets: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ExtendedFormat:
    """Represents a publisher-specific extension of a foundational format."""

    format_id: str
    extends: str
    name: str
    modifications: dict[str, Any] = field(default_factory=dict)

    def apply_to_base(self, base_format: FoundationalFormat) -> dict[str, Any]:
        """Apply modifications to base format and return the extended format."""
        # Start with base format
        extended = {
            "format_id": self.format_id,
            "name": self.name,
            "type": base_format.type,
            "description": f"{self.name} - Extended from {base_format.name}",
            "extends": self.extends,
            "is_standard": False,
            "is_foundational": False,
            "assets": base_format.assets.copy() if base_format.assets else [],
        }

        # Apply modifications to assets
        if "asset_modifications" in self.modifications:
            # Modify existing assets or add new ones
            asset_mods = self.modifications["asset_modifications"]
            for asset_id, changes in asset_mods.items():
                # Find the asset to modify
                for asset in extended["assets"]:
                    if asset.get("asset_id") == asset_id:
                        asset.update(changes)
                        break
                else:
                    # Asset not found, add as new if it has required fields
                    if "asset_type" in changes:
                        changes["asset_id"] = asset_id
                        extended["assets"].append(changes)

        if "additional_assets" in self.modifications:
            # Add new assets
            extended["assets"].extend(self.modifications["additional_assets"])

        if "remove_assets" in self.modifications:
            # Remove specific assets
            remove_ids = set(self.modifications["remove_assets"])
            extended["assets"] = [a for a in extended["assets"] if a.get("asset_id") not in remove_ids]

        return extended


class FoundationalFormatsManager:
    """Manages foundational formats and their extensions."""

    def __init__(self, formats_file: str | None = None):
        """Initialize with foundational formats from JSON file."""
        self.foundational_formats: dict[str, FoundationalFormat] = {}
        self.extended_formats: dict[str, ExtendedFormat] = {}

        # Load foundational formats
        if formats_file is None:
            formats_file = Path(__file__).parent / "data" / "foundational_creative_formats.json"

        self.load_foundational_formats(formats_file)

    def load_foundational_formats(self, formats_file: Path):
        """Load foundational formats from JSON file."""
        try:
            with open(formats_file) as f:
                data = json.load(f)

            for fmt in data.get("foundational_formats", []):
                format_obj = FoundationalFormat(
                    format_id=fmt["format_id"],
                    name=fmt["name"],
                    type=fmt["type"],
                    description=fmt["description"],
                    is_standard=fmt.get("is_standard", True),
                    is_foundational=fmt.get("is_foundational", True),
                    assets=fmt.get("assets", []),
                )
                self.foundational_formats[format_obj.format_id] = format_obj

            logger.info(f"Loaded {len(self.foundational_formats)} foundational formats")

        except Exception as e:
            logger.error(f"Error loading foundational formats: {e}")

    def get_foundational_format(self, format_id: str) -> FoundationalFormat | None:
        """Get a foundational format by ID."""
        return self.foundational_formats.get(format_id)

    def list_foundational_formats(self) -> list[FoundationalFormat]:
        """List all foundational formats."""
        return list(self.foundational_formats.values())

    def create_extension(
        self, format_id: str, extends: str, name: str, modifications: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Create an extended format from a foundational format."""
        base_format = self.get_foundational_format(extends)
        if not base_format:
            logger.error(f"Foundational format {extends} not found")
            return None

        extended = ExtendedFormat(format_id=format_id, extends=extends, name=name, modifications=modifications)

        self.extended_formats[format_id] = extended
        return extended.apply_to_base(base_format)

    def validate_extension(self, extends: str, modifications: dict[str, Any]) -> list[str]:
        """Validate that an extension is compatible with its base format."""
        errors = []

        base_format = self.get_foundational_format(extends)
        if not base_format:
            errors.append(f"Base format {extends} not found")
            return errors

        # Validate dimension modifications
        if "dimensions" in modifications:
            base_dims = base_format.specs.get("base_dimensions", {})
            for platform, _dims in modifications["dimensions"].items():
                if platform not in base_dims and platform not in ["desktop", "tablet", "mobile"]:
                    errors.append(f"Unknown platform: {platform}")

        # Validate that required base specs aren't removed
        if "restrictions" in modifications:
            for key, value in modifications["restrictions"].items():
                if value is None and key in ["file_types", "max_file_size_kb"]:
                    errors.append(f"Cannot remove required spec: {key}")

        return errors

    def suggest_base_format(self, format_specs: dict[str, Any]) -> str | None:
        """Suggest the best foundational format to extend based on specs."""
        # Simple heuristic-based matching
        format_type = format_specs.get("type", "display")

        if format_type == "video":
            return "foundation_universal_video"

        # Check for carousel/multi-product features
        if any(key in format_specs for key in ["product_count", "carousel", "slides"]):
            return "foundation_product_showcase_carousel"

        # Check for expandable features
        if any(key in format_specs for key in ["expandable", "collapsed_state", "expanded_state"]):
            return "foundation_expandable_display"

        # Check for scroll/mobile features
        if any(key in format_specs for key in ["scroll", "parallax", "mobile_first"]):
            return "foundation_scroll_triggered_experience"

        # Default to immersive canvas for responsive formats
        if format_specs.get("responsive") or "viewport" in str(format_specs):
            return "foundation_immersive_canvas"

        return None

    def export_all_formats(self) -> dict[str, Any]:
        """Export all formats (foundational and extended) as a single structure."""
        return {
            "version": "1.0",
            "foundational_formats": [
                {
                    "format_id": fmt.format_id,
                    "name": fmt.name,
                    "type": fmt.type,
                    "description": fmt.description,
                    "is_standard": fmt.is_standard,
                    "is_foundational": fmt.is_foundational,
                    "assets": fmt.assets,
                }
                for fmt in self.foundational_formats.values()
            ],
            "extended_formats": [
                {
                    "format_id": ext.format_id,
                    "extends": ext.extends,
                    "name": ext.name,
                    "modifications": ext.modifications,
                    "resolved": ext.apply_to_base(self.foundational_formats[ext.extends]),
                }
                for ext in self.extended_formats.values()
                if ext.extends in self.foundational_formats
            ],
        }


# Example usage
if __name__ == "__main__":
    # Initialize manager
    manager = FoundationalFormatsManager()

    # List foundational formats
    print("Foundational Formats:")
    for fmt in manager.list_foundational_formats():
        print(f"  - {fmt.format_id}: {fmt.name}")

    # Create NYTimes extension
    nyt_extension = manager.create_extension(
        format_id="nytimes_slideshow_flex_xl",
        extends="foundation_product_showcase_carousel",
        name="NYTimes Slideshow Flex XL",
        modifications={
            "dimensions": {
                "desktop": [{"width": 1125, "height": 600}, {"width": 970, "height": 600}],
                "tablet": {"width": 728, "height": 600},
                "mobile": {"width": 800, "height": 1400},
            },
            "additional_specs": {
                "min_products": 3,
                "max_products": 5,
                "product_image_size": {
                    "desktop": {"width": 600, "height": 600},
                    "tablet": {"width": 600, "height": 600},
                    "mobile": {"width": 600, "height": 600},
                },
                "headlines_per_slide": True,
                "character_limits": {"headline": 100, "descriptor_desktop": 210, "descriptor_mobile": 70},
            },
        },
    )

    print("\nCreated extension:")
    print(json.dumps(nyt_extension, indent=2))
