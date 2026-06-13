import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.types import FileType
from tests.make_markdown_service import make_markdown_service
from tests.stub_extractor import StubExtractor


class TestMarkdownServicePrimarySelection(unittest.TestCase):
    def test_clean_tier_picks_primary_when_matched(self):
        primary = StubExtractor(
            'pymupdf', 'primary-only', confidence=0.99, file_types=(FileType.PDF.value,)
        )
        other = StubExtractor(
            'other', 'other-only', confidence=0.99, file_types=(FileType.PDF.value,)
        )
        service = make_markdown_service([primary, other])
        with mock.patch(
            'doc_to_markdown_core_lib.data_layers.service.markdown_service.detect_tier',
            return_value='clean',
        ):
            result = service.extract(b'%PDF', FileType.PDF.value)
        self.assertEqual(result.markdown, 'primary-only')
        self.assertEqual(result.report['extractors_used'], ['pymupdf'])


if __name__ == '__main__':
    unittest.main()
