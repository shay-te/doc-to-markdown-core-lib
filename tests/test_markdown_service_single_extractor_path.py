import json
import unittest

from doc_to_markdown_core_lib.data_layers.service.types import FileType
from tests.fakes import StubExtractor, make_markdown_service


class TestSingleExtractorPath(unittest.TestCase):
    def test_single_extractor_winner_passes_through(self):
        service = make_markdown_service(
            [
                StubExtractor(
                    'text',
                    'hello world',
                    confidence=0.95,
                    file_types=(FileType.PDF.value,),
                )
            ],
        )
        result = service.extract(b'pdf-bytes', FileType.PDF.value)
        self.assertEqual(result.markdown, 'hello world')
        self.assertEqual(result.report['winning_extractor'], 'text')
        self.assertFalse(result.report['needs_review'])
        self.assertTrue(result.report['completeness_check'])

    def test_utf8_bytes_round_trip(self):
        sample = 'שלום עולם — مرحبا بالعالم — 你好世界'
        service = make_markdown_service(
            [
                StubExtractor(
                    'text', sample, confidence=0.95, file_types=(FileType.PDF.value,)
                )
            ],
        )
        result = service.extract(b'pdf-bytes', FileType.PDF.value)
        self.assertEqual(result.markdown_bytes.decode('utf-8'), sample)
        decoded = json.loads(result.report_bytes.decode('utf-8'))
        self.assertEqual(decoded['languages_detected'], [])

    def test_report_shape_matches_spec(self):
        service = make_markdown_service(
            [
                StubExtractor(
                    'text',
                    'hello',
                    confidence=0.9,
                    file_types=(FileType.PDF.value,),
                    languages=['eng'],
                )
            ],
        )
        report = service.extract(b'x', FileType.PDF.value).report
        self.assertIn('overall_confidence', report)
        self.assertIn('tier', report)
        self.assertIn('extractors_used', report)
        self.assertIn('languages_detected', report)
        self.assertIn('flagged_regions', report)
        self.assertIn('completeness_check', report)
        self.assertEqual(report['languages_detected'], ['eng'])


if __name__ == '__main__':
    unittest.main()
