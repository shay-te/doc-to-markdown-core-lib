"""Branch-coverage fillers — each test targets one specific line/branch."""
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import (
    CandidateSelectionService,
    _agreement,
    _completeness_ok,
    _strip_bom,
    _union_languages,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.docx.docx_extractor import (
    DocxExtractor,
    _docx_table_to_markdown,
)
from doc_to_markdown_core_lib.data_layers.service.markdown_service import (
    MarkdownService,
)
from doc_to_markdown_core_lib.data_layers.service.types import ExtractionCandidate
from tests.fakes import StubExtractor


def _new(extractors):
    return MarkdownService(
        selection_service=CandidateSelectionService(),
        extractors=extractors,
    )


class TestCandidateSelectionHelpers(unittest.TestCase):
    def test_completeness_ok_with_no_candidates_is_false(self):
        self.assertFalse(_completeness_ok('anything', [], floor=0.5))

    def test_completeness_ok_skips_empty_candidates(self):
        candidate = ExtractionCandidate(extractor='empty', markdown='')
        self.assertTrue(_completeness_ok('hello', [candidate], floor=0.5))

    def test_strip_bom_with_none(self):
        self.assertIsNone(_strip_bom(None))
        self.assertEqual(_strip_bom(''), '')

    def test_agreement_with_both_empty_candidates(self):
        candidates = [
            ExtractionCandidate(extractor='a', markdown=''),
            ExtractionCandidate(extractor='b', markdown=''),
        ]
        self.assertEqual(_agreement(candidates), 1.0)

    def test_union_languages_dedupes_across_candidates(self):
        candidates = [
            ExtractionCandidate(
                extractor='a', markdown='m', languages=['eng', 'heb']
            ),
            ExtractionCandidate(
                extractor='b', markdown='m', languages=['heb', 'ara']
            ),
        ]
        self.assertEqual(_union_languages(candidates), ['eng', 'heb', 'ara'])


class TestMarkdownServiceEmptyCandidateSkip(unittest.TestCase):
    def test_extractor_returning_whitespace_is_recorded_as_skipped_empty(self):
        service = _new(
            [
                StubExtractor(
                    'blank', '   ', confidence=0.5, file_types=('pdf',)
                ),
                StubExtractor(
                    'text', 'real text', confidence=0.9, file_types=('pdf',)
                ),
            ],
        )
        result = service.extract(b'%PDF', 'pdf')
        reasons = {
            entry['extractor']: entry['reason']
            for entry in result.report['extractors_skipped']
        }
        self.assertEqual(reasons.get('blank'), 'empty result')


class TestMarkdownServicePrimarySelection(unittest.TestCase):
    def test_clean_tier_picks_primary_when_matched(self):
        primary = StubExtractor(
            'pymupdf', 'primary-only', confidence=0.99, file_types=('pdf',)
        )
        other = StubExtractor(
            'other', 'other-only', confidence=0.99, file_types=('pdf',)
        )
        service = _new([primary, other])
        with mock.patch(
            'doc_to_markdown_core_lib.data_layers.service.markdown_service.detect_tier',
            return_value='clean',
        ):
            result = service.extract(b'%PDF', 'pdf')
        self.assertEqual(result.markdown, 'primary-only')
        self.assertEqual(result.report['extractors_used'], ['pymupdf'])


class TestDocxTableHelper(unittest.TestCase):
    def test_empty_rows_returns_empty_string(self):
        class _Tbl(object):
            rows = []

        self.assertEqual(_docx_table_to_markdown(_Tbl()), '')

    def test_long_row_is_truncated_to_header_width(self):
        class _Cell(object):
            def __init__(self, text):
                self.text = text

        class _Row(object):
            def __init__(self, texts):
                self.cells = [_Cell(text) for text in texts]

        class _Tbl(object):
            def __init__(self, rows):
                self.rows = [_Row(cells) for cells in rows]

        rendered = _docx_table_to_markdown(_Tbl([['A', 'B'], ['1', '2', '3', '4']]))
        self.assertIn('| 1 | 2 |', rendered)
        self.assertNotIn('| 3 |', rendered)


class TestPdfPlumberEmptyTableBranch(unittest.TestCase):
    def test_empty_table_does_not_emit_markdown(self):
        import sys
        import types as _types

        from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pdfplumber_extractor import (
            PdfPlumberExtractor,
        )

        class _Page(object):
            def extract_text(self):
                return 'body'

            def extract_tables(self):
                return [[]]

        class _Pdf(object):
            pages = [_Page()]

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

        plumber_mod = _types.ModuleType('pdfplumber')
        plumber_mod.open = lambda buf: _Pdf()
        with mock.patch.dict(sys.modules, {'pdfplumber': plumber_mod}):
            result = PdfPlumberExtractor().extract(b'%PDF', 'pdf')
        self.assertIn('body', result.markdown)
        self.assertNotIn('|', result.markdown)


class TestDocxEmptyTableBranchInExtract(unittest.TestCase):
    def test_empty_table_in_doc_does_not_emit(self):
        import sys
        import types as _types

        docx_mod = _types.ModuleType('docx')

        class _FakeStyle(object):
            name = ''

        class _FakePara(object):
            text = 'body'
            style = _FakeStyle()

        class _FakeTbl(object):
            rows = []

        class _FakeDoc(object):
            def __init__(self, *a, **kw):
                self.paragraphs = [_FakePara()]
                self.tables = [_FakeTbl()]

        docx_mod.Document = _FakeDoc
        with mock.patch.dict(sys.modules, {'docx': docx_mod}):
            result = DocxExtractor().extract(b'PK', 'docx')
        self.assertEqual(result.markdown, 'body')


class TestMarkdownServiceCleanTierNoPrimaryEntry(unittest.TestCase):
    def test_clean_tier_image_falls_back_to_first_match(self):
        # 'image' isn't in _PRIMARY_PER_TYPE → fall through to matches[:1].
        service = _new(
            [
                StubExtractor(
                    'img-a', 'aaa', confidence=0.9, file_types=('image',)
                ),
                StubExtractor(
                    'img-b', 'bbb', confidence=0.5, file_types=('image',)
                ),
            ],
        )
        with mock.patch(
            'doc_to_markdown_core_lib.data_layers.service.markdown_service.detect_tier',
            return_value='clean',
        ):
            result = service.extract(b'\x89PNG', 'image')
        self.assertEqual(result.markdown, 'aaa')


if __name__ == '__main__':
    unittest.main()
