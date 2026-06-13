"""Shared test doubles: extractor stubs, fake backend modules, builders."""
import sys
import types
from typing import List, Optional
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import (
    CandidateSelectionService,
)
from doc_to_markdown_core_lib.data_layers.service.markdown_service import (
    MarkdownService,
)
from doc_to_markdown_core_lib.data_layers.service.types import (
    ExtractionCandidate,
    ExtractorUnavailable,
    FileType,
)


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


def make_markdown_service(extractors, confidence_threshold=0.8):
    """:class:`MarkdownService` over an explicit extractor list."""
    return MarkdownService(
        selection_service=CandidateSelectionService(
            confidence_threshold=confidence_threshold,
        ),
        extractors=extractors,
    )


def patch_module(module_name, module):
    """Installs ``module`` under ``module_name`` for the ``with`` scope."""
    return mock.patch.dict(sys.modules, {module_name: module})


def make_fitz_module(pages_text=None, open_raises=None, pixmap_bytes=None):
    """Fake PyMuPDF: pages expose text and PNG pixmaps."""
    fitz_module = types.ModuleType('fitz')
    pages_text = pages_text if pages_text is not None else ['hello world']
    pixmap_bytes = pixmap_bytes or b'\x89PNG\r\n\x1a\n' + b'\x00' * 16

    class FakePixmap:
        def tobytes(self, image_format):
            return pixmap_bytes

    class FakePage:
        def __init__(self, text):
            self._text = text

        def get_text(self, mode='text'):
            return self._text

        def get_pixmap(self, dpi=200):
            return FakePixmap()

    class FakeDoc:
        def __init__(self):
            self._pages = [FakePage(text) for text in pages_text]

        def __iter__(self):
            return iter(self._pages)

        def __len__(self):
            return len(self._pages)

        def close(self):
            pass

    def fake_open(stream=None, filetype=None):
        if open_raises is not None:
            raise open_raises
        return FakeDoc()

    fitz_module.open = fake_open
    return fitz_module


def make_pil_modules(open_returns=None):
    """Fake ``PIL`` + ``PIL.Image`` module pair."""
    pil_module = types.ModuleType('PIL')
    image_module = types.ModuleType('PIL.Image')

    class FakeImage:
        def __init__(self, name='img'):
            self.name = name

    image_module.open = mock.Mock(return_value=open_returns or FakeImage())
    pil_module.Image = image_module
    return pil_module, image_module


def make_mammoth_module(text):
    """Fake ``mammoth`` whose ``convert_to_markdown`` returns ``text``."""
    mammoth_module = types.ModuleType('mammoth')

    class Result:
        def __init__(self, value):
            self.value = value

    mammoth_module.convert_to_markdown = lambda file_object: Result(text)
    return mammoth_module
