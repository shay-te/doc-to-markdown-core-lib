import unittest

from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import (
    _assert_utf8,
)


class TestUtf8AssertionRejectsBom(unittest.TestCase):
    def test_assert_utf8_rejects_bom(self):
        with self.assertRaises(ValueError):
            _assert_utf8(b'\xef\xbb\xbfhello')


if __name__ == '__main__':
    unittest.main()
