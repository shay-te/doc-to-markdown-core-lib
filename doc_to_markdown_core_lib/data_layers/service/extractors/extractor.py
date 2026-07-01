from abc import ABC, abstractmethod
from typing import Tuple

from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType


class Extractor(ABC):
    """Engines raise ``ExtractorUnavailable`` from ``extract`` (not
    ``__init__``) so the registry can be built eagerly. The
    ``file_type`` argument is the canonical :class:`FileType` enum
    member — backend libraries that only accept strings (markitdown's
    suffix, soffice's ``--convert-to``, fitz's ``filetype=``) read
    ``file_type.value`` at the call site."""

    name: str = ''
    file_types: Tuple[FileType, ...] = ()

    @abstractmethod
    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        ...  # pragma: no cover
