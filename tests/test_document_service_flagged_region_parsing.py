import unittest

from doc_to_markdown_core_lib.data_layers.data.file_type import FileType
from tests.make_document_service import make_document_service
from tests.stub_extractor import StubExtractor


class TestFlaggedRegionParsing(unittest.TestCase):
    def test_inline_flag_is_parsed_into_report(self):
        marker = '⚠️[UNCERTAIN: hello | candidates: hi | hey]'
        service = make_document_service(
            [
                StubExtractor(
                    'text',
                    f'before {marker} after',
                    confidence=0.95,
                    file_types=(FileType.PDF,),
                )
            ],
        )
        result = service.extract(b'%PDF', FileType.PDF)
        regions = result.report.flagged_regions
        self.assertEqual(len(regions), 1)
        self.assertEqual(regions[0].best_guess, 'hello')
        self.assertEqual(regions[0].candidates, ['hi', 'hey'])
        self.assertTrue(result.report.needs_review)


if __name__ == '__main__':
    unittest.main()
