import unittest

from doc_to_markdown_core_lib.data_layers.service.types import ExtractionResult


class TestExtractionResult(unittest.TestCase):
    def test_default_candidates_is_empty_list(self):
        result = ExtractionResult(
            markdown='m', markdown_bytes=b'm', report={}, report_bytes=b'{}'
        )
        self.assertEqual(result.candidates, [])


if __name__ == '__main__':
    unittest.main()
