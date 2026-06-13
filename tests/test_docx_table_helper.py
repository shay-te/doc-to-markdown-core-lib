import unittest

from doc_to_markdown_core_lib.data_layers.service.extractors.docx.docx_extractor import (
    _docx_table_to_markdown,
)


class TestDocxTableHelper(unittest.TestCase):
    def test_empty_rows_returns_empty_string(self):
        class _Tbl(object):
            rows = []

        self.assertEqual(_docx_table_to_markdown(_Tbl()), '')

    def test_long_row_is_truncated_to_header_width(self):
        class _Cell(object):
            def __init__(self, text):
                self.text = text

        class _Row(object):
            def __init__(self, texts):
                self.cells = [_Cell(text) for text in texts]

        class _Tbl(object):
            def __init__(self, rows):
                self.rows = [_Row(cells) for cells in rows]

        rendered = _docx_table_to_markdown(_Tbl([['A', 'B'], ['1', '2', '3', '4']]))
        self.assertIn('| 1 | 2 |', rendered)
        self.assertNotIn('| 3 |', rendered)


if __name__ == '__main__':
    unittest.main()
