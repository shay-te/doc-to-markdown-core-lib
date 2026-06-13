import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractors.docx.docx_extractor import (
    DocxExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType


class TestDocxEmptyTableBranchInExtract(unittest.TestCase):
    def test_empty_table_in_doc_does_not_emit(self):
        docx_module = types.ModuleType('docx')

        class _FakeStyle(object):
            name = ''

        class _FakePara(object):
            text = 'body'
            style = _FakeStyle()

        class _FakeTbl(object):
            rows = []

        class _FakeDoc(object):
            def __init__(self, *args, **kwargs):
                self.paragraphs = [_FakePara()]
                self.tables = [_FakeTbl()]

        docx_module.Document = _FakeDoc
        with mock.patch.dict(sys.modules, {'docx': docx_module}):
            result = DocxExtractor().extract(b'PK', FileType.DOCX.value)
        self.assertEqual(result.markdown, 'body')


if __name__ == '__main__':
    unittest.main()
