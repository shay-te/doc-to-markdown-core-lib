import dataclasses
import json
import unittest

from doc_to_markdown_core_lib.data_layers.data.file_type import FileType
from tests.make_document_service import make_document_service
from tests.stub_extractor import StubExtractor


class TestSingleExtractorPath(unittest.TestCase):
    def test_single_extractor_winner_passes_through(self):
        service = make_document_service(
            [
                StubExtractor(
                    'text',
                    'hello world',
                    confidence=0.95,
                    file_types=(FileType.PDF,),
                )
            ],
        )
        result = service.extract(b'pdf-bytes', FileType.PDF)
        self.assertEqual(result.markdown, 'hello world')
        self.assertEqual(result.report.winning_extractor, 'text')
        self.assertFalse(result.report.needs_review)
        self.assertTrue(result.report.completeness_check)

    def test_utf8_bytes_round_trip(self):
        sample = 'שלום עולם — مرحبا بالعالم — 你好世界'
        service = make_document_service(
            [
                StubExtractor(
                    'text', sample, confidence=0.95, file_types=(FileType.PDF,)
                )
            ],
        )
        result = service.extract(b'pdf-bytes', FileType.PDF)
        self.assertEqual(result.markdown_bytes.decode('utf-8'), sample)
        decoded = json.loads(result.report_bytes.decode('utf-8'))
        self.assertEqual(decoded['languages_detected'], [])

    def test_report_shape_matches_spec(self):
        service = make_document_service(
            [
                StubExtractor(
                    'text',
                    'hello',
                    confidence=0.9,
                    file_types=(FileType.PDF,),
                    languages=['eng'],
                )
            ],
        )
        report = service.extract(b'x', FileType.PDF).report
        field_names = {report_field.name for report_field in dataclasses.fields(report)}
        self.assertEqual(
            field_names,
            {
                'overall_confidence',
                'tier',
                'extractors_used',
                'extractors_skipped',
                'languages_detected',
                'flagged_regions',
                'completeness_check',
                'winning_extractor',
                'agreement_score',
                'needs_review',
                'source_filename',
            },
        )
        self.assertEqual(report.languages_detected, ['eng'])


if __name__ == '__main__':
    unittest.main()
