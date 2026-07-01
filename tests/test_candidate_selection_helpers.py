import unittest

from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import (
    _agreement,
    _completeness_ok,
    _strip_bom,
    _tokenize,
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

    def test_completeness_flags_winner_missing_consensus(self):
        # Two extractors agree on the full text; the winner truncated it.
        candidates = [
            ExtractionCandidate(extractor='a', markdown='alpha'),
            ExtractionCandidate(extractor='b', markdown='alpha beta gamma delta'),
            ExtractionCandidate(extractor='c', markdown='alpha beta gamma delta'),
        ]
        self.assertFalse(_completeness_ok('alpha', candidates, floor=0.6))

    def test_completeness_ignores_lone_junk_candidate(self):
        # A single extractor's junk is not consensus, so the clean winner
        # is NOT flagged incomplete for dropping it.
        candidates = [
            ExtractionCandidate(extractor='clean', markdown='real body text here'),
            ExtractionCandidate(extractor='junk', markdown='99 PAGE 1 footer 99'),
        ]
        self.assertTrue(
            _completeness_ok('real body text here', candidates, floor=0.6)
        )

    def test_completeness_ok_when_three_extractors_all_disagree(self):
        # 3 fully-disjoint outputs → no consensus to be missing → not flagged
        # incomplete; the low agreement score carries the disagreement signal.
        candidates = [
            ExtractionCandidate(extractor='a', markdown='apple'),
            ExtractionCandidate(extractor='b', markdown='zebra'),
            ExtractionCandidate(extractor='c', markdown='mango'),
        ]
        self.assertTrue(_completeness_ok('apple', candidates, floor=0.6))

    def test_completeness_vacuous_with_only_two_extractors(self):
        # Truncation is undetectable with <3 extractors (winner ⊇ consensus);
        # completeness defers to the agreement score, so it returns True here.
        candidates = [
            ExtractionCandidate(extractor='a', markdown='alpha'),
            ExtractionCandidate(extractor='b', markdown='alpha beta gamma delta'),
        ]
        self.assertTrue(_completeness_ok('alpha', candidates, floor=0.6))

    def test_tokenize_splits_cjk_per_char_latin_per_word(self):
        self.assertEqual(_tokenize('hello world'), ['hello', 'world'])
        self.assertEqual(_tokenize('你好世界'), ['你', '好', '世', '界'])

    def test_agreement_high_for_cjk_differing_only_in_whitespace(self):
        # Same CJK content, different line breaks — must NOT tank agreement.
        candidates = [
            ExtractionCandidate(extractor='a', markdown='你好世界程序'),
            ExtractionCandidate(extractor='b', markdown='你好 世界\n程序'),
        ]
        self.assertEqual(_agreement(candidates), 1.0)

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
