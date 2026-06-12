"""Adapter tests. Backend libraries are mocked in ``sys.modules``."""
import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractors.docx.docx_extractor import DocxExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.docx.mammoth_extractor import MammothExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.md.md_extractor import MdExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pdfminer_extractor import PdfMinerExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pdfplumber_extractor import (
    PdfPlumberExtractor,
    _table_to_markdown as _plumber_table_to_md,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pymupdf_extractor import PyMuPdfExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.image.tesseract_extractor import TesseractExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.txt.txt_extractor import TxtExtractor
from doc_to_markdown_core_lib.data_layers.service.types import ExtractorUnavailable



def _patch(name, mod):
    return mock.patch.dict(sys.modules, {name: mod})


def _make_fitz(pages_text=None, open_raises=None, pixmap_bytes=None):
    mod = types.ModuleType('fitz')
    pages_text = pages_text if pages_text is not None else ['hello world']
    pixmap_bytes = pixmap_bytes or b'\x89PNG\r\n\x1a\n' + b'\x00' * 16

    class FakePixmap:
        def tobytes(self, fmt):
            return pixmap_bytes

    class FakePage:
        def __init__(self, text):
            self._text = text

        def get_text(self, mode='text'):
            return self._text

        def get_pixmap(self, dpi=200):
            return FakePixmap()

    class FakeDoc:
        def __init__(self):
            self._pages = [FakePage(text) for text in pages_text]

        def __iter__(self):
            return iter(self._pages)

        def __len__(self):
            return len(self._pages)

        def close(self):
            pass

    def fake_open(stream=None, filetype=None):
        if open_raises:
            raise open_raises
        return FakeDoc()

    mod.open = fake_open
    return mod


def _make_pil(open_returns=None):
    pil = types.ModuleType('PIL')
    image = types.ModuleType('PIL.Image')

    class FakeImage:
        def __init__(self, name='img'):
            self.name = name

    image.open = mock.Mock(return_value=open_returns or FakeImage())
    pil.Image = image
    return pil, image



class TestMdExtractor(unittest.TestCase):
    def test_pass_through_utf8(self):
        result = MdExtractor().extract('שלום\nworld'.encode('utf-8'), 'md')
        self.assertEqual(result.markdown, 'שלום\nworld')
        self.assertEqual(result.confidence, 1.0)

    def test_strips_bom(self):
        result = MdExtractor().extract('﻿hello'.encode('utf-8'), 'md')
        self.assertEqual(result.markdown, 'hello')



class TestTxtExtractor(unittest.TestCase):
    def test_utf8(self):
        result = TxtExtractor().extract('مرحبا'.encode('utf-8'), 'txt')
        self.assertEqual(result.markdown, 'مرحبا')
        self.assertEqual(result.confidence, 1.0)

    def test_utf16(self):
        result = TxtExtractor().extract('hello'.encode('utf-16'), 'txt')
        self.assertEqual(result.markdown, 'hello')
        self.assertEqual(result.confidence, 1.0)

    def test_falls_back_to_latin1(self):
        # 0xa3 is invalid utf-8 and odd-length for utf-16 → latin-1 branch.
        result = TxtExtractor().extract(b'\xa3', 'txt')
        self.assertEqual(result.confidence, 0.5)
        self.assertIn('£', result.markdown)



class TestPyMuPdfExtractor(unittest.TestCase):
    def test_unavailable_without_fitz(self):
        with mock.patch.dict(sys.modules, {'fitz': None}):
            with self.assertRaises(ExtractorUnavailable):
                PyMuPdfExtractor().extract(b'%PDF', 'pdf')

    def test_happy_path(self):
        with _patch('fitz', _make_fitz(['page one text', 'page two text'])):
            result = PyMuPdfExtractor().extract(b'%PDF', 'pdf')
        self.assertIn('page one text', result.markdown)
        self.assertIn('page two text', result.markdown)
        self.assertIn('page 1', result.markdown)
        self.assertIn('page 2', result.markdown)
        self.assertGreater(result.confidence, 0.0)

    def test_open_failure_raises_runtime_error(self):
        with _patch('fitz', _make_fitz(open_raises=Exception('broken'))):
            with self.assertRaises(RuntimeError):
                PyMuPdfExtractor().extract(b'%PDF', 'pdf')



class _FakePdfPlumberPage:
    def __init__(self, text, tables=None):
        self._text = text
        self._tables = tables or []

    def extract_text(self):
        return self._text

    def extract_tables(self):
        return self._tables


class _FakePdfPlumberPdf:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass


def _make_pdfplumber(pages):
    mod = types.ModuleType('pdfplumber')
    mod.open = lambda buf: _FakePdfPlumberPdf(pages)
    return mod


class TestPdfPlumberExtractor(unittest.TestCase):
    def test_unavailable_without_pdfplumber(self):
        with mock.patch.dict(sys.modules, {'pdfplumber': None}):
            with self.assertRaises(ExtractorUnavailable):
                PdfPlumberExtractor().extract(b'%PDF', 'pdf')

    def test_happy_path_with_tables(self):
        pages = [
            _FakePdfPlumberPage(
                'p1 body',
                tables=[[['A', 'B'], ['1', '2'], ['3', '4', 'extra']]],
            ),
            _FakePdfPlumberPage('p2 body'),
        ]
        with _patch('pdfplumber', _make_pdfplumber(pages)):
            result = PdfPlumberExtractor().extract(b'%PDF', 'pdf')
        self.assertIn('p1 body', result.markdown)
        self.assertIn('p2 body', result.markdown)
        self.assertIn('| A | B |', result.markdown)

    def test_table_helper_empty_returns_empty_string(self):
        self.assertEqual(_plumber_table_to_md([]), '')
        self.assertEqual(_plumber_table_to_md([[]]), '')

    def test_table_helper_pads_short_rows(self):
        rendered = _plumber_table_to_md([['A', 'B', 'C'], ['1']])
        self.assertIn('| 1 |  |  |', rendered)



class TestPdfMinerExtractor(unittest.TestCase):
    def test_unavailable_without_pdfminer(self):
        with mock.patch.dict(sys.modules, {'pdfminer': None, 'pdfminer.high_level': None}):
            with self.assertRaises(ExtractorUnavailable):
                PdfMinerExtractor().extract(b'%PDF', 'pdf')

    def test_happy_path(self):
        high_level = types.ModuleType('pdfminer.high_level')
        high_level.extract_text = lambda buf: 'extracted text from pdf'
        pdfminer = types.ModuleType('pdfminer')
        pdfminer.high_level = high_level
        with mock.patch.dict(
            sys.modules, {'pdfminer': pdfminer, 'pdfminer.high_level': high_level}
        ):
            result = PdfMinerExtractor().extract(b'%PDF', 'pdf')
        self.assertEqual(result.markdown, 'extracted text from pdf')



def _make_pytesseract(text='ocr text'):
    mod = types.ModuleType('pytesseract')
    mod.image_to_string = mock.Mock(return_value=text)
    return mod


class TestTesseractExtractor(unittest.TestCase):
    def test_unavailable_without_pytesseract(self):
        with mock.patch.dict(sys.modules, {'pytesseract': None}):
            with self.assertRaises(ExtractorUnavailable):
                TesseractExtractor().extract(b'\x89PNG', 'image')

    def test_image_happy_path(self):
        pytesseract = _make_pytesseract(text='hello from ocr')
        pil, image = _make_pil()
        with mock.patch.dict(
            sys.modules, {'pytesseract': pytesseract, 'PIL': pil, 'PIL.Image': image}
        ):
            result = TesseractExtractor(languages=['eng', 'heb']).extract(
                b'\x89PNG', 'image'
            )
        self.assertEqual(result.markdown, 'hello from ocr')
        self.assertEqual(result.languages, ['eng', 'heb'])
        # ensure the lang arg threaded through
        pytesseract.image_to_string.assert_called_once()
        self.assertEqual(pytesseract.image_to_string.call_args.kwargs['lang'], 'eng+heb')

    def test_pdf_happy_path_uses_fitz(self):
        pytesseract = _make_pytesseract(text='page-ocr')
        pil, image = _make_pil()
        fitz = _make_fitz(pages_text=['', ''])
        with mock.patch.dict(
            sys.modules,
            {
                'pytesseract': pytesseract,
                'PIL': pil,
                'PIL.Image': image,
                'fitz': fitz,
            },
        ):
            result = TesseractExtractor().extract(b'%PDF', 'pdf')
        self.assertIn('page-ocr', result.markdown)
        self.assertIn('page 1', result.markdown)

    def test_pdf_requires_fitz(self):
        pytesseract = _make_pytesseract()
        pil, image = _make_pil()
        with mock.patch.dict(
            sys.modules,
            {
                'pytesseract': pytesseract,
                'PIL': pil,
                'PIL.Image': image,
                'fitz': None,
            },
        ):
            with self.assertRaises(ExtractorUnavailable):
                TesseractExtractor().extract(b'%PDF', 'pdf')

    def test_unknown_file_type_raises_value_error(self):
        pytesseract = _make_pytesseract()
        pil, image = _make_pil()
        with mock.patch.dict(
            sys.modules, {'pytesseract': pytesseract, 'PIL': pil, 'PIL.Image': image}
        ):
            with self.assertRaises(ValueError):
                TesseractExtractor().extract(b'x', 'audio')



def _make_docx(paragraphs, tables=None):
    docx_mod = types.ModuleType('docx')

    class FakeStyle:
        def __init__(self, name):
            self.name = name

    class FakePara:
        def __init__(self, text, style_name=''):
            self.text = text
            self.style = FakeStyle(style_name) if style_name else FakeStyle('')

    class FakeCell:
        def __init__(self, text):
            self.text = text

    class FakeRow:
        def __init__(self, cells):
            self.cells = [FakeCell(text) for text in cells]

    class FakeTable:
        def __init__(self, rows):
            self.rows = [FakeRow(cells) for cells in rows]

    class FakeDoc:
        def __init__(self, *a, **kw):
            self.paragraphs = [FakePara(t, s) for t, s in paragraphs]
            self.tables = [FakeTable(table_rows) for table_rows in (tables or [])]

    docx_mod.Document = FakeDoc
    return docx_mod


class TestDocxExtractor(unittest.TestCase):
    def test_unavailable_without_docx(self):
        with mock.patch.dict(sys.modules, {'docx': None}):
            with self.assertRaises(ExtractorUnavailable):
                DocxExtractor().extract(b'PK', 'docx')

    def test_headings_lists_paragraphs_and_tables(self):
        paragraphs = [
            ('Title', 'Heading 1'),
            ('Sub', 'Heading 2'),
            ('Subsub', 'Heading 3'),
            ('Detail', 'Heading 4'),
            ('Body text', ''),
            ('item', 'List Bullet'),
            ('', 'Normal'),  # empty — skipped
        ]
        tables = [[['A', 'B'], ['1', '2'], ['short']]]
        with _patch('docx', _make_docx(paragraphs, tables)):
            result = DocxExtractor().extract(b'PK', 'docx')
        md = result.markdown
        self.assertIn('# Title', md)
        self.assertIn('## Sub', md)
        self.assertIn('### Subsub', md)
        self.assertIn('#### Detail', md)
        self.assertIn('Body text', md)
        self.assertIn('- item', md)
        self.assertIn('| A | B |', md)
        self.assertIn('| short |  |', md)

    def test_no_paragraphs_yields_zero_confidence(self):
        with _patch('docx', _make_docx([], [])):
            result = DocxExtractor().extract(b'PK', 'docx')
        self.assertEqual(result.markdown, '')
        self.assertEqual(result.confidence, 0.0)



def _make_mammoth(text):
    mod = types.ModuleType('mammoth')

    class Result:
        def __init__(self, value):
            self.value = value

    mod.convert_to_markdown = lambda buf: Result(text)
    return mod


class TestMammothExtractor(unittest.TestCase):
    def test_unavailable_without_mammoth(self):
        with mock.patch.dict(sys.modules, {'mammoth': None}):
            with self.assertRaises(ExtractorUnavailable):
                MammothExtractor().extract(b'PK', 'docx')

    def test_happy_path(self):
        with _patch('mammoth', _make_mammoth('# heading\n\nbody')):
            result = MammothExtractor().extract(b'PK', 'docx')
        self.assertIn('# heading', result.markdown)
        self.assertGreater(result.confidence, 0.0)

    def test_empty_value_gives_zero_confidence(self):
        with _patch('mammoth', _make_mammoth('')):
            result = MammothExtractor().extract(b'PK', 'docx')
        self.assertEqual(result.confidence, 0.0)


if __name__ == '__main__':
    unittest.main()
