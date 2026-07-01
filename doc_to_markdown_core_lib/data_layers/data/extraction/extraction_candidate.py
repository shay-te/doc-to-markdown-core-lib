from dataclasses import dataclass, field
from typing import List


@dataclass
class ExtractionCandidate:
    """One engine's verdict. ``confidence`` is the engine's 0..1
    self-assessment."""
    extractor: str
    markdown: str
    confidence: float = 0.0
    languages: List[str] = field(default_factory=list)
