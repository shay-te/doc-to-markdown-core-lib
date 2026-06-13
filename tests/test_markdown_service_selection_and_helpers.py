import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.file_type import FileType
from tests.make_markdown_service import make_markdown_service
from tests.stub_extractor import StubExtractor


class TestSelectionAndHelpers(unittest.TestCase):
    def test_clean_tier_with_no_primary_match_returns_first_match(self):
        service = make_markdown_service(
            [
                StubExtractor(
                    'a', 'text-a', confidence=0.9, file_types=(FileType.PDF,)
                ),
                StubExtractor(
                    'b', 'text-b', confidence=0.5, file_types=(FileType.PDF,)
                ),
            ],
        )
        with mock.patch(
            'doc_to_markdown_core_lib.data_layers.service.markdown_service.detect_tier',
            return_value='clean',
        ):
            result = service.extract(b'x', FileType.PDF)
        # 'pymupdf' (the primary) isn't in our list → matches[:1] used.
        self.assertEqual(result.markdown, 'text-a')

    def test_strip_bom_in_winning_output(self):
        service = make_markdown_service(
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

    def test_completeness_failure_appends_tail_flag(self):
        # Disjoint candidates — survival check fails → tail flag.
        service = make_markdown_service(
            [
                StubExtractor(
                    'a', 'apple', confidence=0.9, file_types=(FileType.PDF,)
                ),
                StubExtractor(
                    'b',
                    'zebra giraffe lion',
                    confidence=0.8,
                    file_types=(FileType.PDF,),
                ),
            ],
        )
        result = service.extract(b'x', FileType.PDF)
        self.assertFalse(result.report['completeness_check'])
        self.assertIn('extraction may be incomplete', result.markdown)
        self.assertTrue(result.report['needs_review'])


if __name__ == '__main__':
    unittest.main()
