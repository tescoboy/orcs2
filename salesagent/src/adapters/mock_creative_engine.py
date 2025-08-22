from datetime import datetime, timedelta
from typing import Any

from src.adapters.creative_engine import CreativeEngineAdapter
from src.core.schemas import Creative, CreativeAdaptation, CreativeStatus


class MockCreativeEngine(CreativeEngineAdapter):
    """A mock creative engine that simulates a simple approval and adaptation workflow."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.human_review_required = config.get("human_review_required", True)
        self.adaptation_time_days = config.get("adaptation_time_days", 3)
        # Formats that can be auto-approved
        self.auto_approve_formats = set(config.get("auto_approve_formats", []))

    def process_creatives(self, creatives: list[Creative]) -> list[CreativeStatus]:
        """Simulates processing creatives, returning their status."""
        processed = []
        for creative in creatives:
            # Check if format is auto-approvable
            is_auto_approvable = creative.format_id in self.auto_approve_formats

            # Determine status based on format and configuration
            if is_auto_approvable and not self.human_review_required:
                status = "approved"
                detail = f"Creative auto-approved - format '{creative.format_id}' is in auto-approve list."
                est_approval = None
            elif is_auto_approvable and self.human_review_required:
                # Even with human review required, auto-approve formats bypass it
                status = "approved"
                detail = f"Creative auto-approved - format '{creative.format_id}' bypasses human review."
                est_approval = None
            else:
                # Requires human review
                status = "pending_review"
                detail = f"Awaiting manual review - format '{creative.format_id}' requires human approval."
                est_approval = datetime.now().astimezone() + timedelta(days=2)

            # Generate adaptation suggestions for video formats
            suggested_adaptations = []
            if creative.format_id and "video" in creative.format_id.lower():
                # Suggest vertical version for horizontal videos
                if "16x9" in creative.format_id or "horizontal" in creative.format_id:
                    suggested_adaptations.append(
                        CreativeAdaptation(
                            adaptation_id=f"adapt_{creative.creative_id}_vertical",
                            format_id="video_vertical_9x16",
                            name="Mobile Vertical Version",
                            description="9:16 vertical version optimized for mobile feeds",
                            changes_summary=[
                                "Crop to 9:16 aspect ratio focusing on key visual elements",
                                "Add captions for sound-off viewing (85% of mobile users)",
                                "Optimize for 6-second hook to capture attention",
                            ],
                            rationale="Mobile inventory converts 35% better with vertical format and represents 60% of available impressions",
                            estimated_performance_lift=35.0,
                        )
                    )
                # Suggest shorter version for long videos
                if creative.metadata and creative.metadata.get("duration", 0) > 15:
                    suggested_adaptations.append(
                        CreativeAdaptation(
                            adaptation_id=f"adapt_{creative.creative_id}_6s",
                            format_id="video_6s_bumper",
                            name="6-Second Bumper Version",
                            description="Short-form version for bumper inventory",
                            changes_summary=[
                                "Cut to 6-second duration focusing on key message",
                                "Add brand logo throughout",
                                "Optimize for non-skippable format",
                            ],
                            rationale="6-second bumpers have 95% completion rate and lower CPM",
                            estimated_performance_lift=25.0,
                        )
                    )

            processed.append(
                CreativeStatus(
                    creative_id=creative.creative_id,
                    status=status,
                    detail=detail,
                    estimated_approval_time=est_approval,
                    suggested_adaptations=suggested_adaptations,
                )
            )
        return processed
