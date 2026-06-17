import unittest

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
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


if __name__ == '__main__':
    unittest.main()
