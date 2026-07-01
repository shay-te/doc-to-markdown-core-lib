from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FlaggedRegion:
    """A span the selection service flagged for human review — an inline
    UNCERTAIN marker or a completeness gap. Part of the extraction report.
    """
    location: str
    best_guess: str = ''
    candidates: List[str] = field(default_factory=list)
    reason: Optional[str] = None
