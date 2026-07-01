import unittest

from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_candidate import (
    ExtractionCandidate,
)


class TestExtractionCandidate(unittest.TestCase):
    def test_default_languages_is_empty_list(self):
        candidate = ExtractionCandidate(extractor='x', markdown='m')
        self.assertEqual(candidate.languages, [])
        self.assertEqual(candidate.confidence, 0.0)

    def test_two_candidates_have_independent_default_lists(self):
        first_candidate = ExtractionCandidate(extractor='a', markdown='m')
        second_candidate = ExtractionCandidate(extractor='b', markdown='m')
        first_candidate.languages.append('eng')
        # dataclass default_factory works — second list is untouched
        self.assertEqual(second_candidate.languages, [])


if __name__ == '__main__':
    unittest.main()
