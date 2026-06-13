import unittest

from doc_to_markdown_core_lib.data_layers.service.types import FileType
from tests.fakes import StubExtractor, make_markdown_service


class TestMultipleExtractorsPickWinner(unittest.TestCase):
    def test_highest_confidence_candidate_wins(self):
        service = make_markdown_service(
            [
                StubExtractor(
                    'a',
                    'apple banana',
                    confidence=0.7,
                    file_types=(FileType.PDF.value,),
                ),
                StubExtractor(
                    'b',
                    'apple banana carrot',
                    confidence=0.9,
                    file_types=(FileType.PDF.value,),
                ),
            ],
        )
        result = service.extract(b'pdf', FileType.PDF.value)
        self.assertEqual(result.markdown, 'apple banana carrot')
        self.assertEqual(result.report['winning_extractor'], 'b')

    def test_disagreement_drives_needs_review(self):
        service = make_markdown_service(
            [
                StubExtractor(
                    'a',
                    'apple banana carrot',
                    confidence=0.9,
                    file_types=(FileType.PDF.value,),
                ),
                StubExtractor(
                    'b',
                    'zebra giraffe lion',
                    confidence=0.9,
                    file_types=(FileType.PDF.value,),
                ),
            ],
            confidence_threshold=0.8,
        )
        result = service.extract(b'pdf', FileType.PDF.value)
        self.assertTrue(result.report['needs_review'])


if __name__ == '__main__':
    unittest.main()
