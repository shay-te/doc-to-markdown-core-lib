import unittest

from doc_to_markdown_core_lib.data_layers.service.types import FileType
from tests.make_markdown_service import make_markdown_service
from tests.stub_extractor import StubExtractor


class TestMarkdownServiceEmptyCandidateSkip(unittest.TestCase):
    def test_extractor_returning_whitespace_is_recorded_as_skipped_empty(self):
        service = make_markdown_service(
            [
                StubExtractor(
                    'blank', '   ', confidence=0.5, file_types=(FileType.PDF.value,)
                ),
                StubExtractor(
                    'text', 'real text', confidence=0.9, file_types=(FileType.PDF.value,)
                ),
            ],
        )
        result = service.extract(b'%PDF', FileType.PDF.value)
        reasons = {
            entry['extractor']: entry['reason']
            for entry in result.report['extractors_skipped']
        }
        self.assertEqual(reasons.get('blank'), 'empty result')


if __name__ == '__main__':
    unittest.main()
