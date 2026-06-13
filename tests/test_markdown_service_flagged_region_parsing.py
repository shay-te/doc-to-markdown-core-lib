import unittest

from doc_to_markdown_core_lib.data_layers.service.types import FileType
from tests.fakes import StubExtractor, make_markdown_service


class TestFlaggedRegionParsing(unittest.TestCase):
    def test_inline_flag_is_parsed_into_report(self):
        marker = '⚠️[UNCERTAIN: hello | candidates: hi | hey]'
        service = make_markdown_service(
            [
                StubExtractor(
                    'text',
                    f'before {marker} after',
                    confidence=0.95,
                    file_types=(FileType.PDF.value,),
                )
            ],
        )
        result = service.extract(b'pdf', FileType.PDF.value)
        regions = result.report['flagged_regions']
        self.assertEqual(len(regions), 1)
        self.assertEqual(regions[0]['best_guess'], 'hello')
        self.assertEqual(regions[0]['candidates'], ['hi', 'hey'])
        self.assertTrue(result.report['needs_review'])


if __name__ == '__main__':
    unittest.main()
