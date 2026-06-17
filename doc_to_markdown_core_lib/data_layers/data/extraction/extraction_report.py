from dataclasses import dataclass, field
from typing import List, Optional

from doc_to_markdown_core_lib.data_layers.data.tier import Tier


@dataclass
class ExtractionReport:
    """The run report the selection service emits alongside the winning
    markdown — the audit trail explaining the choice. Serialized to JSON
    (``extraction_report.json``) via :func:`dataclasses.asdict`.
    """
    overall_confidence: float
    tier: Tier
    extractors_used: List[str]
    extractors_skipped: List[dict]
    languages_detected: List[str]
    flagged_regions: List[dict]
    completeness_check: bool
    winning_extractor: Optional[str]
    agreement_score: float
    needs_review: bool
    source_filename: Optional[str] = None
