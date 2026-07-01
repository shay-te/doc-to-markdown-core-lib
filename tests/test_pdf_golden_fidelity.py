import difflib
import os
import re
import unittest

from doc_to_markdown_core_lib.data_layers.data.file_type import FileType
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pymupdf_extractor import (
    PyMuPdfExtractor,
)
from tests.make_document_service import make_document_service
from tests.stub_extractor import StubExtractor

try:
    import fitz  # noqa: F401  (PyMuPDF)
    _HAS_FITZ = True
except ImportError:
    _HAS_FITZ = False

_FIXTURE_DIR = os.path.join(
    os.path.dirname(__file__), 'data', 'books', 'eugene_schwartz'
)
_BASENAME = 'eugene_schwartz_lost_secrets_lecture_not_full_book'

# Real text-layer extraction of this scanned lecture lands ~0.95 against the
# hand-sourced golden transcript; floor it below that to catch regressions
# without being brittle across PyMuPDF versions. The gap is the two
# newspaper-image pages, which only OCR (already wired for PDF) recovers.
MIN_TEXT_FIDELITY = 0.90
_IMAGE_PAGE_TEXT_CEILING = 200


def _read_bytes(ext):
    with open(os.path.join(_FIXTURE_DIR, _BASENAME + ext), 'rb') as handle:
        return handle.read()


def _read_text(ext):
    with open(
        os.path.join(_FIXTURE_DIR, _BASENAME + ext), encoding='utf-8'
    ) as handle:
        return handle.read()


def _text_only(markdown):
    """Compare TEXT fidelity, not layout: drop page markers, fold whitespace."""
    without_markers = re.sub(r'<!--.*?-->', ' ', markdown, flags=re.DOTALL)
    return ' '.join(without_markers.split()).lower()


def _fidelity(markdown):
    return difflib.SequenceMatcher(
        None, _text_only(markdown), _text_only(_read_text('.txt'))
    ).ratio()


@unittest.skipUnless(_HAS_FITZ, 'PyMuPDF (fitz) not installed')
class TestPdfGoldenFidelity(unittest.TestCase):
    """Regression guard on real PDF extraction quality, measured against a
    hand-sourced golden transcript of a hard scanned lecture. Runs the real
    PyMuPDF extractor, so it is skipped wherever fitz is absent."""

    def test_pymupdf_text_fidelity_against_golden(self):
        candidate = PyMuPdfExtractor().extract(_read_bytes('.pdf'), FileType.PDF)
        ratio = _fidelity(candidate.markdown)
        self.assertGreaterEqual(
            ratio,
            MIN_TEXT_FIDELITY,
            f'PDF text fidelity {ratio:.4f} fell below {MIN_TEXT_FIDELITY}',
        )

    def test_vote_keeps_text_winner_when_noisy_ocr_also_present(self):
        # Exercises the full service path (tier → fan-out → vote → report).
        # Real measurement: full-doc OCR of this mostly-text PDF is far noisier
        # (~0.60) than the text layer (~0.95), yet both saturate confidence at
        # 1.0 — so the clean winner survives only because text extractors
        # precede OCR in the lineup. This pins that ordering; reversing it
        # would ship the OCR noise.
        noisy_ocr = StubExtractor(
            'rapidocr', 'ocr noise word ' * 200, file_types=(FileType.PDF,)
        )
        service = make_document_service([PyMuPdfExtractor(), noisy_ocr])
        result = service.extract(_read_bytes('.pdf'), FileType.PDF)
        self.assertEqual(result.report.winning_extractor, 'pymupdf')
        self.assertGreaterEqual(_fidelity(result.markdown), MIN_TEXT_FIDELITY)

    def test_fixture_exercises_image_pages_that_need_ocr(self):
        # Confirms this is a real hard candidate: some pages carry their text
        # in a raster image the text layer can't see, so OCR is what closes
        # the remaining gap. Keeps the fixture honest if it is ever swapped.
        doc = fitz.open(stream=_read_bytes('.pdf'), filetype=FileType.PDF)
        try:
            image_pages = sum(
                1
                for page in doc
                if len((page.get_text('text') or '').strip())
                < _IMAGE_PAGE_TEXT_CEILING
                and page.get_images()
            )
        finally:
            doc.close()
        self.assertGreaterEqual(image_pages, 1)


if __name__ == '__main__':
    unittest.main()
