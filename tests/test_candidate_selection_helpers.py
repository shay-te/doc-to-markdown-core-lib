import unittest

from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import (
    _agreement,
    _completeness_ok,
    _strip_bom,
    _union_languages,
)
from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_candidate import (
    ExtractionCandidate,
)


class TestCandidateSelectionHelpers(unittest.TestCase):
    def test_completeness_ok_with_no_candidates_is_false(self):
        self.assertFalse(_completeness_ok('anything', [], floor=0.5))

    def test_completeness_ok_skips_empty_candidates(self):
        candidate = ExtractionCandidate(extractor='empty', markdown='')
        self.assertTrue(_completeness_ok('hello', [candidate], floor=0.5))

    def test_strip_bom_with_none(self):
        self.assertIsNone(_strip_bom(None))
        self.assertEqual(_strip_bom(''), '')

    def test_agreement_with_both_empty_candidates(self):
        candidates = [
            ExtractionCandidate(extractor='a', markdown=''),
            ExtractionCandidate(extractor='b', markdown=''),
        ]
        self.assertEqual(_agreement(candidates), 1.0)

    def test_union_languages_dedupes_across_candidates(self):
        candidates = [
            ExtractionCandidate(
                extractor='a', markdown='m', languages=['eng', 'heb']
            ),
            ExtractionCandidate(
                extractor='b', markdown='m', languages=['heb', 'ara']
            ),
        ]
        self.assertEqual(_union_languages(candidates), ['eng', 'heb', 'ara'])


if __name__ == '__main__':
    unittest.main()
