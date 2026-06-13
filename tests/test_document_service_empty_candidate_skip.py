import unittest

from doc_to_markdown_core_lib.data_layers.service.file_type import FileType
from tests.make_document_service import make_document_service
from tests.stub_extractor import StubExtractor


class TestDocumentServiceEmptyCandidateSkip(unittest.TestCase):
    def test_extractor_returning_whitespace_is_recorded_as_skipped_empty(self):
        service = make_document_service(
            [
                StubExtractor(
                    'blank', '   ', confidence=0.5, file_types=(FileType.PDF,)
                ),
                StubExtractor(
                    'text', 'real text', confidence=0.9, file_types=(FileType.PDF,)
                ),
            ],
        )
        result = service.extract(b'%PDF', FileType.PDF)
        reasons = {
            entry['extractor']: entry['reason']
            for entry in result.report['extractors_skipped']
        }
        self.assertEqual(reasons.get('blank'), 'empty result')


if __name__ == '__main__':
    unittest.main()
