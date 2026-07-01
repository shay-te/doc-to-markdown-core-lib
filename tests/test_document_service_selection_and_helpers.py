import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.data.file_type import FileType
from doc_to_markdown_core_lib.data_layers.data.tier import Tier
from tests.make_document_service import make_document_service
from tests.stub_extractor import StubExtractor


class TestSelectionAndHelpers(unittest.TestCase):
    def test_clean_tier_still_fans_out_to_all_matching_extractors(self):
        # Tier no longer prunes the lineup: even a CLEAN-tier doc runs every
        # matching extractor and the selection service votes on the winner.
        service = make_document_service(
            [
                StubExtractor(
                    'a', 'text alpha', confidence=0.9, file_types=(FileType.PDF,)
                ),
                StubExtractor(
                    'b', 'text beta', confidence=0.5, file_types=(FileType.PDF,)
                ),
            ],
        )
        with mock.patch(
            'doc_to_markdown_core_lib.data_layers.service.document_service.detect_tier',
            return_value=Tier.CLEAN,
        ):
            result = service.extract(b'x', FileType.PDF)
        self.assertEqual(sorted(result.report.extractors_used), ['a', 'b'])
        self.assertEqual(result.report.winning_extractor, 'a')

    def test_strip_bom_in_winning_output(self):
        service = make_document_service(
            [
                StubExtractor(
                    'text',
                    '﻿hello with bom',
                    confidence=0.95,
                    file_types=(FileType.PDF,),
                )
            ],
        )
        result = service.extract(b'x', FileType.PDF)
        self.assertFalse(result.markdown_bytes.startswith(b'\xef\xbb\xbf'))
        self.assertEqual(result.markdown, 'hello with bom')

    def test_saturated_tie_breaks_toward_corroborated_output(self):
        # All three saturate confidence at 1.0. Two text extractors agree; a
        # noisy OCR shares nothing. Despite the OCR being registered FIRST,
        # the corroborated output wins — selection is by merit, not lineup
        # order (guards the Finding-A fix).
        shared = 'alpha beta gamma delta echo foxtrot golf hotel india juliet'
        service = make_document_service(
            [
                StubExtractor(
                    'rapidocr', 'zzz yyy xxx www', confidence=1.0,
                    file_types=(FileType.PDF,),
                ),
                StubExtractor(
                    'pymupdf', shared, confidence=1.0, file_types=(FileType.PDF,)
                ),
                StubExtractor(
                    'pdfplumber', shared, confidence=1.0, file_types=(FileType.PDF,)
                ),
            ],
        )
        result = service.extract(b'x', FileType.PDF)
        self.assertIn(result.report.winning_extractor, ('pymupdf', 'pdfplumber'))
        self.assertNotEqual(result.report.winning_extractor, 'rapidocr')

    def test_completeness_failure_appends_tail_flag(self):
        # Winner is highest-confidence but truncated; two other extractors
        # agree on the full content → chosen misses the consensus → tail flag.
        service = make_document_service(
            [
                StubExtractor(
                    'a', 'alpha', confidence=0.9, file_types=(FileType.PDF,)
                ),
                StubExtractor(
                    'b',
                    'alpha beta gamma delta echo foxtrot',
                    confidence=0.8,
                    file_types=(FileType.PDF,),
                ),
                StubExtractor(
                    'c',
                    'alpha beta gamma delta echo foxtrot',
                    confidence=0.7,
                    file_types=(FileType.PDF,),
                ),
            ],
        )
        result = service.extract(b'x', FileType.PDF)
        self.assertEqual(result.report.winning_extractor, 'a')
        self.assertFalse(result.report.completeness_check)
        self.assertIn('extraction may be incomplete', result.markdown)
        self.assertTrue(result.report.needs_review)


if __name__ == '__main__':
    unittest.main()
