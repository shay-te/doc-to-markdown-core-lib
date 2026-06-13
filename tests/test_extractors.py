"""Adapter tests. Backend libraries are mocked in ``sys.modules``."""
import os
import subprocess
import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractors.doc.soffice_extractor import SofficeExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.doc.textract_extractor import (
    TextractExtractor,
    _PLAIN_TEXT_CONFIDENCE_DISCOUNT,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.docx.docx_extractor import DocxExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.docx.mammoth_extractor import MammothExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.image.easyocr_extractor import EasyOcrExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.image.rapidocr_extractor import RapidOcrExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.md.md_extractor import MdExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.markitdown_extractor import MarkItDownExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pdfminer_extractor import PdfMinerExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pymupdf4llm_extractor import PyMuPdf4LlmExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pypdf_extractor import PypdfExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pdfplumber_extractor import (
    PdfPlumberExtractor,
    _table_to_markdown as _plumber_table_to_md,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pymupdf_extractor import PyMuPdfExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.image.tesseract_extractor import TesseractExtractor
from doc_to_markdown_core_lib.data_layers.service.extractors.txt.txt_extractor import TxtExtractor
from doc_to_markdown_core_lib.data_layers.service.types import (
    ExtractorUnavailable,
    FileType,
)

_SOFFICE_MODULE = (
    'doc_to_markdown_core_lib.data_layers.service.extractors.doc.soffice_extractor'
)



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
        result = MdExtractor().extract('שלום\nworld'.encode('utf-8'), FileType.MD.value)
        self.assertEqual(result.markdown, 'שלום\nworld')
        self.assertEqual(result.confidence, 1.0)

    def test_strips_bom(self):
        result = MdExtractor().extract('﻿hello'.encode('utf-8'), FileType.MD.value)
        self.assertEqual(result.markdown, 'hello')



class TestTxtExtractor(unittest.TestCase):
    def test_utf8(self):
        result = TxtExtractor().extract('مرحبا'.encode('utf-8'), FileType.TXT.value)
        self.assertEqual(result.markdown, 'مرحبا')
        self.assertEqual(result.confidence, 1.0)

    def test_utf16(self):
        result = TxtExtractor().extract('hello'.encode('utf-16'), FileType.TXT.value)
        self.assertEqual(result.markdown, 'hello')
        self.assertEqual(result.confidence, 1.0)

    def test_falls_back_to_latin1(self):
        # 0xa3 is invalid utf-8 and odd-length for utf-16 → latin-1 branch.
        result = TxtExtractor().extract(b'\xa3', FileType.TXT.value)
        self.assertEqual(result.confidence, 0.5)
        self.assertIn('£', result.markdown)



class TestPyMuPdfExtractor(unittest.TestCase):
    def test_unavailable_without_fitz(self):
        with mock.patch.dict(sys.modules, {'fitz': None}):
            with self.assertRaises(ExtractorUnavailable):
                PyMuPdfExtractor().extract(b'%PDF', FileType.PDF.value)

    def test_happy_path(self):
        with _patch('fitz', _make_fitz(['page one text', 'page two text'])):
            result = PyMuPdfExtractor().extract(b'%PDF', FileType.PDF.value)
        self.assertIn('page one text', result.markdown)
        self.assertIn('page two text', result.markdown)
        self.assertIn('page 1', result.markdown)
        self.assertIn('page 2', result.markdown)
        self.assertGreater(result.confidence, 0.0)

    def test_open_failure_raises_runtime_error(self):
        with _patch('fitz', _make_fitz(open_raises=Exception('broken'))):
            with self.assertRaises(RuntimeError):
                PyMuPdfExtractor().extract(b'%PDF', FileType.PDF.value)



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
                PdfPlumberExtractor().extract(b'%PDF', FileType.PDF.value)

    def test_happy_path_with_tables(self):
        pages = [
            _FakePdfPlumberPage(
                'p1 body',
                tables=[[['A', 'B'], ['1', '2'], ['3', '4', 'extra']]],
            ),
            _FakePdfPlumberPage('p2 body'),
        ]
        with _patch('pdfplumber', _make_pdfplumber(pages)):
            result = PdfPlumberExtractor().extract(b'%PDF', FileType.PDF.value)
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
                PdfMinerExtractor().extract(b'%PDF', FileType.PDF.value)

    def test_happy_path(self):
        high_level = types.ModuleType('pdfminer.high_level')
        high_level.extract_text = lambda buf: 'extracted text from pdf'
        pdfminer = types.ModuleType('pdfminer')
        pdfminer.high_level = high_level
        with mock.patch.dict(
            sys.modules, {'pdfminer': pdfminer, 'pdfminer.high_level': high_level}
        ):
            result = PdfMinerExtractor().extract(b'%PDF', FileType.PDF.value)
        self.assertEqual(result.markdown, 'extracted text from pdf')



def _make_pytesseract(text='ocr text'):
    mod = types.ModuleType('pytesseract')
    mod.image_to_string = mock.Mock(return_value=text)
    return mod


class TestTesseractExtractor(unittest.TestCase):
    def test_unavailable_without_pytesseract(self):
        with mock.patch.dict(sys.modules, {'pytesseract': None}):
            with self.assertRaises(ExtractorUnavailable):
                TesseractExtractor().extract(b'\x89PNG', FileType.IMAGE.value)

    def test_image_happy_path(self):
        pytesseract = _make_pytesseract(text='hello from ocr')
        pil, image = _make_pil()
        with mock.patch.dict(
            sys.modules, {'pytesseract': pytesseract, 'PIL': pil, 'PIL.Image': image}
        ):
            result = TesseractExtractor(languages=['eng', 'heb']).extract(
                b'\x89PNG', FileType.IMAGE.value
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
            result = TesseractExtractor().extract(b'%PDF', FileType.PDF.value)
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
                TesseractExtractor().extract(b'%PDF', FileType.PDF.value)

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
        def __init__(self, *args, **kwargs):
            self.paragraphs = [
                FakePara(para_text, style_name)
                for para_text, style_name in paragraphs
            ]
            self.tables = [FakeTable(table_rows) for table_rows in (tables or [])]

    docx_mod.Document = FakeDoc
    return docx_mod


class TestDocxExtractor(unittest.TestCase):
    def test_unavailable_without_docx(self):
        with mock.patch.dict(sys.modules, {'docx': None}):
            with self.assertRaises(ExtractorUnavailable):
                DocxExtractor().extract(b'PK', FileType.DOCX.value)

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
            result = DocxExtractor().extract(b'PK', FileType.DOCX.value)
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
            result = DocxExtractor().extract(b'PK', FileType.DOCX.value)
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
                MammothExtractor().extract(b'PK', FileType.DOCX.value)

    def test_happy_path(self):
        with _patch('mammoth', _make_mammoth('# heading\n\nbody')):
            result = MammothExtractor().extract(b'PK', FileType.DOCX.value)
        self.assertIn('# heading', result.markdown)
        self.assertGreater(result.confidence, 0.0)

    def test_empty_value_gives_zero_confidence(self):
        with _patch('mammoth', _make_mammoth('')):
            result = MammothExtractor().extract(b'PK', FileType.DOCX.value)
        self.assertEqual(result.confidence, 0.0)



def _make_textract(process_result: bytes):
    mod = types.ModuleType('textract')
    mod.process = mock.Mock(return_value=process_result)
    return mod


class TestTextractExtractor(unittest.TestCase):
    def test_unavailable_without_textract(self):
        with mock.patch.dict(sys.modules, {'textract': None}):
            with self.assertRaises(ExtractorUnavailable):
                TextractExtractor().extract(b'\xd0\xcf', FileType.DOC.value)

    def test_doc_happy_path_uses_doc_suffix(self):
        textract = _make_textract(b'legacy doc body')
        with _patch('textract', textract):
            result = TextractExtractor().extract(b'\xd0\xcf', FileType.DOC.value)
        self.assertEqual(result.markdown, 'legacy doc body')
        self.assertGreater(result.confidence, 0.0)
        processed_path = textract.process.call_args.args[0]
        self.assertTrue(processed_path.endswith('.doc'))
        # the temp file must be cleaned up after processing
        self.assertFalse(os.path.exists(processed_path))

    def test_docx_uses_docx_suffix(self):
        textract = _make_textract(b'docx body')
        with _patch('textract', textract):
            TextractExtractor().extract(b'PK', FileType.DOCX.value)
        processed_path = textract.process.call_args.args[0]
        self.assertTrue(processed_path.endswith('.docx'))

    def test_full_length_text_caps_at_discounted_confidence(self):
        long_text = ('word ' * 1000).encode('utf-8')
        with _patch('textract', _make_textract(long_text)):
            result = TextractExtractor().extract(b'\xd0\xcf', FileType.DOC.value)
        self.assertAlmostEqual(
            result.confidence, _PLAIN_TEXT_CONFIDENCE_DISCOUNT
        )



def _fake_soffice_run(command, **kwargs):
    output_dir = command[command.index('--outdir') + 1]
    with open(os.path.join(output_dir, 'input.docx'), 'wb') as output_file:
        output_file.write(b'PK-converted-docx')


class TestSofficeExtractor(unittest.TestCase):
    def test_unavailable_without_binary(self):
        with mock.patch(f'{_SOFFICE_MODULE}.shutil.which', return_value=None):
            with self.assertRaises(ExtractorUnavailable):
                SofficeExtractor().extract(b'\xd0\xcf', FileType.DOC.value)

    def test_conversion_failure_raises_unavailable(self):
        def failing_run(command, **kwargs):
            raise subprocess.CalledProcessError(returncode=1, cmd=command)

        with mock.patch(
            f'{_SOFFICE_MODULE}.shutil.which', return_value='/usr/bin/soffice'
        ), mock.patch(
            f'{_SOFFICE_MODULE}.subprocess.run', side_effect=failing_run
        ):
            with self.assertRaises(ExtractorUnavailable):
                SofficeExtractor().extract(b'\xd0\xcf', FileType.DOC.value)

    def test_missing_output_file_raises_unavailable(self):
        with mock.patch(
            f'{_SOFFICE_MODULE}.shutil.which', return_value='/usr/bin/soffice'
        ), mock.patch(
            f'{_SOFFICE_MODULE}.subprocess.run', return_value=None
        ):
            with self.assertRaises(ExtractorUnavailable):
                SofficeExtractor().extract(b'\xd0\xcf', FileType.DOC.value)

    def test_happy_path_hands_converted_docx_to_mammoth(self):
        with mock.patch(
            f'{_SOFFICE_MODULE}.shutil.which', return_value='/usr/bin/soffice'
        ), mock.patch(
            f'{_SOFFICE_MODULE}.subprocess.run', side_effect=_fake_soffice_run
        ), _patch('mammoth', _make_mammoth('# converted heading')):
            result = SofficeExtractor().extract(b'\xd0\xcf', FileType.DOC.value)
        self.assertIn('# converted heading', result.markdown)
        self.assertGreater(result.confidence, 0.0)

    def test_without_mammoth_yields_empty_zero_confidence_candidate(self):
        with mock.patch(
            f'{_SOFFICE_MODULE}.shutil.which', return_value='/usr/bin/soffice'
        ), mock.patch(
            f'{_SOFFICE_MODULE}.subprocess.run', side_effect=_fake_soffice_run
        ), mock.patch.dict(sys.modules, {'mammoth': None}):
            result = SofficeExtractor().extract(b'\xd0\xcf', FileType.DOC.value)
        self.assertEqual(result.markdown, '')
        self.assertEqual(result.confidence, 0.0)



def _make_pypdf(pages_text):
    mod = types.ModuleType('pypdf')

    class FakePage:
        def __init__(self, text):
            self._text = text

        def extract_text(self):
            return self._text

    class FakeReader:
        def __init__(self, stream):
            self.pages = [FakePage(text) for text in pages_text]

    mod.PdfReader = FakeReader
    return mod


class TestPypdfExtractor(unittest.TestCase):
    def test_unavailable_without_pypdf(self):
        with mock.patch.dict(sys.modules, {'pypdf': None}):
            with self.assertRaises(ExtractorUnavailable):
                PypdfExtractor().extract(b'%PDF', FileType.PDF.value)

    def test_happy_path(self):
        with _patch('pypdf', _make_pypdf(['first page', 'second page'])):
            result = PypdfExtractor().extract(b'%PDF', FileType.PDF.value)
        self.assertIn('first page', result.markdown)
        self.assertIn('second page', result.markdown)
        self.assertIn('page 1', result.markdown)
        self.assertIn('page 2', result.markdown)
        self.assertGreater(result.confidence, 0.0)



class TestPyMuPdf4LlmExtractor(unittest.TestCase):
    def test_unavailable_without_pymupdf4llm(self):
        with mock.patch.dict(
            sys.modules, {'fitz': _make_fitz(), 'pymupdf4llm': None}
        ):
            with self.assertRaises(ExtractorUnavailable):
                PyMuPdf4LlmExtractor().extract(b'%PDF', FileType.PDF.value)

    def test_happy_path_returns_native_markdown(self):
        pymupdf4llm = types.ModuleType('pymupdf4llm')
        pymupdf4llm.to_markdown = mock.Mock(return_value='# Native\n\nbody')
        with mock.patch.dict(
            sys.modules, {'fitz': _make_fitz(), 'pymupdf4llm': pymupdf4llm}
        ):
            result = PyMuPdf4LlmExtractor().extract(b'%PDF', FileType.PDF.value)
        self.assertIn('# Native', result.markdown)
        self.assertGreater(result.confidence, 0.0)
        pymupdf4llm.to_markdown.assert_called_once()



def _make_markitdown(text_content):
    mod = types.ModuleType('markitdown')

    class FakeConversion:
        def __init__(self, text):
            self.text_content = text

    class FakeMarkItDown:
        last_converted_path = None

        def convert(self, path):
            FakeMarkItDown.last_converted_path = path
            return FakeConversion(text_content)

    mod.MarkItDown = FakeMarkItDown
    return mod


class TestMarkItDownExtractor(unittest.TestCase):
    def test_unavailable_without_markitdown(self):
        with mock.patch.dict(sys.modules, {'markitdown': None}):
            with self.assertRaises(ExtractorUnavailable):
                MarkItDownExtractor().extract(b'%PDF', FileType.PDF.value)

    def test_pdf_happy_path_and_temp_cleanup(self):
        markitdown = _make_markitdown('# converted')
        with _patch('markitdown', markitdown):
            result = MarkItDownExtractor().extract(b'%PDF', FileType.PDF.value)
        self.assertIn('# converted', result.markdown)
        converted_path = markitdown.MarkItDown.last_converted_path
        self.assertTrue(converted_path.endswith('.pdf'))
        self.assertFalse(os.path.exists(converted_path))

    def test_docx_uses_docx_suffix(self):
        markitdown = _make_markitdown('docx body')
        with _patch('markitdown', markitdown):
            MarkItDownExtractor().extract(b'PK', FileType.DOCX.value)
        converted_path = markitdown.MarkItDown.last_converted_path
        self.assertTrue(converted_path.endswith('.docx'))

    def test_unknown_file_type_raises_value_error(self):
        with _patch('markitdown', _make_markitdown('x')):
            with self.assertRaises(ValueError):
                MarkItDownExtractor().extract(b'x', 'audio')



def _make_easyocr(lines, reader_init_raises=None):
    mod = types.ModuleType('easyocr')

    class FakeReader:
        def __init__(self, languages, verbose=False):
            if reader_init_raises:
                raise reader_init_raises
            self.languages = languages

        def readtext(self, image_bytes, detail=0, paragraph=True):
            return lines

    mod.Reader = FakeReader
    return mod


class TestEasyOcrExtractor(unittest.TestCase):
    def test_unavailable_without_easyocr(self):
        with mock.patch.dict(sys.modules, {'easyocr': None}):
            with self.assertRaises(ExtractorUnavailable):
                EasyOcrExtractor().extract(b'\x89PNG', FileType.IMAGE.value)

    def test_reader_init_failure_is_unavailable(self):
        broken = _make_easyocr([], reader_init_raises=ValueError('bad lang combo'))
        with _patch('easyocr', broken):
            with self.assertRaises(ExtractorUnavailable):
                EasyOcrExtractor(languages=['he', 'ch_sim']).extract(
                    b'\x89PNG', FileType.IMAGE.value
                )

    def test_image_happy_path(self):
        with _patch('easyocr', _make_easyocr(['hello', 'world'])):
            result = EasyOcrExtractor(languages=['en']).extract(
                b'\x89PNG', FileType.IMAGE.value
            )
        self.assertEqual(result.markdown, 'hello\nworld')
        self.assertEqual(result.languages, ['en'])
        self.assertGreater(result.confidence, 0.0)

    def test_pdf_happy_path_rasterizes_via_fitz(self):
        with mock.patch.dict(
            sys.modules,
            {
                'easyocr': _make_easyocr(['page-ocr']),
                'fitz': _make_fitz(pages_text=['', '']),
            },
        ):
            result = EasyOcrExtractor().extract(b'%PDF', FileType.PDF.value)
        self.assertIn('page-ocr', result.markdown)
        self.assertIn('page 1', result.markdown)
        self.assertIn('page 2', result.markdown)

    def test_pdf_requires_fitz(self):
        with mock.patch.dict(
            sys.modules, {'easyocr': _make_easyocr(['x']), 'fitz': None}
        ):
            with self.assertRaises(ExtractorUnavailable):
                EasyOcrExtractor().extract(b'%PDF', FileType.PDF.value)

    def test_unknown_file_type_raises_value_error(self):
        with _patch('easyocr', _make_easyocr(['x'])):
            with self.assertRaises(ValueError):
                EasyOcrExtractor().extract(b'x', 'audio')



def _make_rapidocr(detections):
    mod = types.ModuleType('rapidocr_onnxruntime')

    class FakeRapidOCR:
        def __call__(self, image_bytes):
            return detections, 0.01

    mod.RapidOCR = FakeRapidOCR
    return mod


class TestRapidOcrExtractor(unittest.TestCase):
    def test_unavailable_without_rapidocr(self):
        with mock.patch.dict(sys.modules, {'rapidocr_onnxruntime': None}):
            with self.assertRaises(ExtractorUnavailable):
                RapidOcrExtractor().extract(b'\x89PNG', FileType.IMAGE.value)

    def test_image_happy_path(self):
        detections = [
            [[[0, 0]], 'first line', 0.98],
            [[[0, 1]], 'second line', 0.91],
        ]
        with _patch('rapidocr_onnxruntime', _make_rapidocr(detections)):
            result = RapidOcrExtractor().extract(b'\x89PNG', FileType.IMAGE.value)
        self.assertEqual(result.markdown, 'first line\nsecond line')
        self.assertGreater(result.confidence, 0.0)

    def test_no_detections_yields_empty_candidate(self):
        with _patch('rapidocr_onnxruntime', _make_rapidocr(None)):
            result = RapidOcrExtractor().extract(b'\x89PNG', FileType.IMAGE.value)
        self.assertEqual(result.markdown, '')
        self.assertEqual(result.confidence, 0.0)

    def test_pdf_happy_path_rasterizes_via_fitz(self):
        detections = [[[[0, 0]], 'scanned text', 0.9]]
        with mock.patch.dict(
            sys.modules,
            {
                'rapidocr_onnxruntime': _make_rapidocr(detections),
                'fitz': _make_fitz(pages_text=['']),
            },
        ):
            result = RapidOcrExtractor().extract(b'%PDF', FileType.PDF.value)
        self.assertIn('scanned text', result.markdown)
        self.assertIn('page 1', result.markdown)

    def test_unknown_file_type_raises_value_error(self):
        with _patch('rapidocr_onnxruntime', _make_rapidocr([])):
            with self.assertRaises(ValueError):
                RapidOcrExtractor().extract(b'x', 'audio')


if __name__ == '__main__':
    unittest.main()
