"""Re-export module preserving exact backward compatibility."""
from app.services.pipeline_service import (
    PipelineService,
    compute_baselines,
    compute_trend,
    compute_zscores,
    evaluate_alert,
    run_pipeline_for_patient,
)

__all__ = [
    "PipelineService",
    "compute_baselines",
    "compute_trend",
    "compute_zscores",
    "evaluate_alert",
    "run_pipeline_for_patient",
]
