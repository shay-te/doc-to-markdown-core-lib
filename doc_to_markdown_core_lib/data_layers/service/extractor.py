from abc import ABC, abstractmethod
from typing import Tuple

from doc_to_markdown_core_lib.data_layers.service.extraction_candidate import (
    ExtractionCandidate,
)


class Extractor(ABC):
    """Engines raise ``ExtractorUnavailable`` from ``extract`` (not
    ``__init__``) so the registry can be built eagerly."""

    name: str = ''
    file_types: Tuple[str, ...] = ()

    @abstractmethod
    def extract(self, content: bytes, file_type: str) -> ExtractionCandidate:
        ...  # pragma: no cover
