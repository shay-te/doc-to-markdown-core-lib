import unittest

from doc_to_markdown_core_lib.data_layers.service.file_type import FileType
from tests.make_markdown_service import make_markdown_service
from tests.stub_extractor import StubExtractor


class TestFailingExtractors(unittest.TestCase):
    def test_failing_extractor_does_not_drop_document(self):
        service = make_markdown_service(
            [
                StubExtractor('boom', '', file_types=(FileType.PDF.value,), raises=True),
                StubExtractor(
                    'text', 'hello', confidence=0.9, file_types=(FileType.PDF.value,)
                ),
            ],
        )
        result = service.extract(b'pdf', FileType.PDF.value)
        self.assertEqual(result.markdown, 'hello')
        self.assertEqual(result.report['extractors_used'], ['text'])
        skipped_names = [
            entry['extractor'] for entry in result.report['extractors_skipped']
        ]
        self.assertIn('boom', skipped_names)

    def test_unavailable_extractor_is_skipped_gracefully(self):
        service = make_markdown_service(
            [
                StubExtractor(
                    'missing-lib', '', file_types=(FileType.PDF.value,), unavailable=True
                ),
                StubExtractor(
                    'text', 'hello', confidence=0.9, file_types=(FileType.PDF.value,)
                ),
            ],
        )
        result = service.extract(b'pdf', FileType.PDF.value)
        reasons = {
            entry['extractor']: entry['reason']
            for entry in result.report['extractors_skipped']
        }
        self.assertIn('missing-lib', reasons)
        self.assertTrue(reasons['missing-lib'].startswith('unavailable:'))

    def test_no_candidates_returns_uncertain_marker(self):
        service = make_markdown_service([])
        result = service.extract(b'pdf', FileType.PDF.value)
        self.assertIn('⚠️[UNCERTAIN', result.markdown)
        self.assertFalse(result.report['completeness_check'])
        self.assertTrue(result.report['needs_review'])


if __name__ == '__main__':
    unittest.main()
