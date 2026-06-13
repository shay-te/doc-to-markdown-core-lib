import json
import unittest

from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import (
    CandidateSelectionService,
)
from doc_to_markdown_core_lib.data_layers.service.markdown_service import (
    MarkdownService as MarkdownExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.types import FileType
from tests.fakes import StubExtractor


def _new(extractors, *, threshold=0.8):
    return MarkdownExtractor(
        selection_service=CandidateSelectionService(
            confidence_threshold=threshold,
        ),
        extractors=extractors,
    )


class TestSingleExtractorPath(unittest.TestCase):
    def test_single_extractor_winner_passes_through(self):
        extractor = _new(
            [
                StubExtractor(
                    'text', 'hello world', confidence=0.95, file_types=(FileType.PDF.value,)
                )
            ],
        )
        result = extractor.extract(b'pdf-bytes', FileType.PDF.value)
        self.assertEqual(result.markdown, 'hello world')
        self.assertEqual(result.report['winning_extractor'], 'text')
        self.assertFalse(result.report['needs_review'])
        self.assertTrue(result.report['completeness_check'])

    def test_utf8_bytes_round_trip(self):
        sample = 'שלום עולם — مرحبا بالعالم — 你好世界'
        extractor = _new(
            [StubExtractor('text', sample, confidence=0.95, file_types=(FileType.PDF.value,))],
        )
        result = extractor.extract(b'pdf-bytes', FileType.PDF.value)
        self.assertEqual(result.markdown_bytes.decode('utf-8'), sample)
        decoded = json.loads(result.report_bytes.decode('utf-8'))
        self.assertEqual(decoded['languages_detected'], [])

    def test_report_shape_matches_spec(self):
        extractor = _new(
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
        report = extractor.extract(b'x', FileType.PDF.value).report
        self.assertIn('overall_confidence', report)
        self.assertIn('tier', report)
        self.assertIn('extractors_used', report)
        self.assertIn('languages_detected', report)
        self.assertIn('flagged_regions', report)
        self.assertIn('completeness_check', report)
        self.assertEqual(report['languages_detected'], ['eng'])


class TestMultipleExtractorsPickWinner(unittest.TestCase):
    def test_highest_confidence_candidate_wins(self):
        extractor = _new(
            [
                StubExtractor(
                    'a', 'apple banana', confidence=0.7, file_types=(FileType.PDF.value,)
                ),
                StubExtractor(
                    'b',
                    'apple banana carrot',
                    confidence=0.9,
                    file_types=(FileType.PDF.value,),
                ),
            ],
        )
        result = extractor.extract(b'pdf', FileType.PDF.value)
        self.assertEqual(result.markdown, 'apple banana carrot')
        self.assertEqual(result.report['winning_extractor'], 'b')

    def test_disagreement_drives_needs_review(self):
        extractor = _new(
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
            threshold=0.8,
        )
        result = extractor.extract(b'pdf', FileType.PDF.value)
        self.assertTrue(result.report['needs_review'])


class TestFailingExtractors(unittest.TestCase):
    def test_failing_extractor_does_not_drop_document(self):
        extractor = _new(
            [
                StubExtractor('boom', '', file_types=(FileType.PDF.value,), raises=True),
                StubExtractor('text', 'hello', confidence=0.9, file_types=(FileType.PDF.value,)),
            ],
        )
        result = extractor.extract(b'pdf', FileType.PDF.value)
        self.assertEqual(result.markdown, 'hello')
        self.assertEqual(result.report['extractors_used'], ['text'])
        skipped_names = [
            entry['extractor'] for entry in result.report['extractors_skipped']
        ]
        self.assertIn('boom', skipped_names)

    def test_unavailable_extractor_is_skipped_gracefully(self):
        extractor = _new(
            [
                StubExtractor(
                    'missing-lib', '', file_types=(FileType.PDF.value,), unavailable=True
                ),
                StubExtractor('text', 'hello', confidence=0.9, file_types=(FileType.PDF.value,)),
            ],
        )
        result = extractor.extract(b'pdf', FileType.PDF.value)
        reasons = {
            entry['extractor']: entry['reason']
            for entry in result.report['extractors_skipped']
        }
        self.assertIn('missing-lib', reasons)
        self.assertTrue(reasons['missing-lib'].startswith('unavailable:'))

    def test_no_candidates_returns_uncertain_marker(self):
        extractor = _new([])
        result = extractor.extract(b'pdf', FileType.PDF.value)
        self.assertIn('⚠️[UNCERTAIN', result.markdown)
        self.assertFalse(result.report['completeness_check'])
        self.assertTrue(result.report['needs_review'])


class TestFlaggedRegionParsing(unittest.TestCase):
    def test_inline_flag_is_parsed_into_report(self):
        marker = '⚠️[UNCERTAIN: hello | candidates: hi | hey]'
        extractor = _new(
            [
                StubExtractor(
                    'text',
                    f'before {marker} after',
                    confidence=0.95,
                    file_types=(FileType.PDF.value,),
                )
            ],
        )
        result = extractor.extract(b'pdf', FileType.PDF.value)
        regions = result.report['flagged_regions']
        self.assertEqual(len(regions), 1)
        self.assertEqual(regions[0]['best_guess'], 'hello')
        self.assertEqual(regions[0]['candidates'], ['hi', 'hey'])
        self.assertTrue(result.report['needs_review'])


class TestSelectionAndHelpers(unittest.TestCase):
    def test_clean_tier_with_no_primary_match_returns_first_match(self):
        extractor = _new(
            [
                StubExtractor('a', 'text-a', confidence=0.9, file_types=(FileType.PDF.value,)),
                StubExtractor('b', 'text-b', confidence=0.5, file_types=(FileType.PDF.value,)),
            ],
        )
        from unittest import mock as _mock

        with _mock.patch(
            'doc_to_markdown_core_lib.data_layers.service.markdown_service.detect_tier',
            return_value='clean',
        ):
            result = extractor.extract(b'x', FileType.PDF.value)
        # 'pymupdf' (the primary) isn't in our list → matches[:1] used.
        self.assertEqual(result.markdown, 'text-a')

    def test_strip_bom_in_winning_output(self):
        extractor = _new(
            [
                StubExtractor(
                    'text',
                    '﻿hello with bom',
                    confidence=0.95,
                    file_types=(FileType.PDF.value,),
                )
            ],
        )
        result = extractor.extract(b'x', FileType.PDF.value)
        self.assertFalse(result.markdown_bytes.startswith(b'\xef\xbb\xbf'))
        self.assertEqual(result.markdown, 'hello with bom')

    def test_completeness_failure_appends_tail_flag(self):
        # Disjoint candidates — survival check fails → tail flag.
        extractor = _new(
            [
                StubExtractor('a', 'apple', confidence=0.9, file_types=(FileType.PDF.value,)),
                StubExtractor(
                    'b',
                    'zebra giraffe lion',
                    confidence=0.8,
                    file_types=(FileType.PDF.value,),
                ),
            ],
        )
        result = extractor.extract(b'x', FileType.PDF.value)
        self.assertFalse(result.report['completeness_check'])
        self.assertIn('extraction may be incomplete', result.markdown)
        self.assertTrue(result.report['needs_review'])


class TestUtf8AssertionRejectsBom(unittest.TestCase):
    def test_assert_utf8_rejects_bom(self):
        from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import _assert_utf8

        with self.assertRaises(ValueError):
            _assert_utf8(b'\xef\xbb\xbfhello')


if __name__ == '__main__':
    unittest.main()
