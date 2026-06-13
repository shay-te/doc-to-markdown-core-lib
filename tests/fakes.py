"""Test doubles for the :class:`Extractor` interface."""
from typing import List, Optional

from doc_to_markdown_core_lib.data_layers.service.types import FileType


class StubExtractor(object):
    """Returns a canned :class:`ExtractionCandidate`."""

    def __init__(
        self,
        name: str,
        markdown: str,
        confidence: float = 1.0,
        languages: Optional[List[str]] = None,
        file_types: tuple = (
            FileType.PDF.value,
            FileType.DOCX.value,
            FileType.IMAGE.value,
            FileType.TXT.value,
            FileType.MD.value,
        ),
        raises: bool = False,
        unavailable: bool = False,
    ):
        self.name = name
        self.file_types = file_types
        self._markdown = markdown
        self._confidence = confidence
        self._languages = languages or []
        self._raises = raises
        self._unavailable = unavailable

    def extract(self, content, file_type):
        from doc_to_markdown_core_lib.data_layers.service.types import (
            ExtractionCandidate,
            ExtractorUnavailable,
        )

        if self._unavailable:
            raise ExtractorUnavailable(f'{self.name}: stub marked unavailable')
        if self._raises:
            raise RuntimeError('boom')
        return ExtractionCandidate(
            extractor=self.name,
            markdown=self._markdown,
            confidence=self._confidence,
            languages=list(self._languages),
        )
