import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.file_type import FileType
from doc_to_markdown_core_lib.data_layers.service.tier import Tier
from tests.make_document_service import make_document_service
from tests.stub_extractor import StubExtractor


class TestDocumentServicePrimarySelection(unittest.TestCase):
    def test_clean_tier_picks_primary_when_matched(self):
        primary = StubExtractor(
            'pymupdf', 'primary-only', confidence=0.99, file_types=(FileType.PDF,)
        )
        other = StubExtractor(
            'other', 'other-only', confidence=0.99, file_types=(FileType.PDF,)
        )
        service = make_document_service([primary, other])
        with mock.patch(
            'doc_to_markdown_core_lib.data_layers.service.document_service.detect_tier',
            return_value=Tier.CLEAN,
        ):
            result = service.extract(b'%PDF', FileType.PDF)
        self.assertEqual(result.markdown, 'primary-only')
        self.assertEqual(result.report['extractors_used'], ['pymupdf'])


if __name__ == '__main__':
    unittest.main()
