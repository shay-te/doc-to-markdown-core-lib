import unittest

from doc_to_markdown_core_lib.data_layers.service.types import (
    ExtractionCandidate,
    ExtractionResult,
    Extractor,
    ExtractorUnavailable,
)


class TestExtractorUnavailable(unittest.TestCase):
    def test_is_runtime_error(self):
        self.assertTrue(issubclass(ExtractorUnavailable, RuntimeError))

    def test_carries_message(self):
        try:
            raise ExtractorUnavailable('missing thing')
        except ExtractorUnavailable as unavailable_error:
            self.assertIn('missing', str(unavailable_error))


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


class TestExtractionResult(unittest.TestCase):
    def test_default_candidates_is_empty_list(self):
        result = ExtractionResult(
            markdown='m', markdown_bytes=b'm', report={}, report_bytes=b'{}'
        )
        self.assertEqual(result.candidates, [])


class TestExtractorAbstract(unittest.TestCase):
    def test_cannot_instantiate_directly(self):
        with self.assertRaises(TypeError):
            Extractor()  # type: ignore[abstract]


if __name__ == '__main__':
    unittest.main()
