"""The shared fixtures under ``tests/data/`` must keep their magic
bytes intact — every extractor test that loads one assumes the file
looks like the format it claims to be."""
import unittest

from tests.read_fixture import read_fixture


class TestFixturesWellFormed(unittest.TestCase):
    def test_pdf_has_pdf_magic(self):
        payload = read_fixture('sample.pdf')
        self.assertTrue(payload.startswith(b'%PDF-'))
        self.assertIn(b'%%EOF', payload)

    def test_docx_is_zip_with_word_document(self):
        # DOCX is a ZIP; the local-file-header magic is PK\x03\x04 and
        # the central directory must reference ``word/document.xml``.
        payload = read_fixture('sample.docx')
        self.assertTrue(payload.startswith(b'PK\x03\x04'))
        self.assertIn(b'word/document.xml', payload)

    def test_png_has_png_signature(self):
        payload = read_fixture('sample.png')
        self.assertTrue(payload.startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertIn(b'IEND', payload)

    def test_md_decodes_as_utf8_markdown(self):
        text = read_fixture('sample.md').decode('utf-8')
        self.assertTrue(text.startswith('# '))

    def test_txt_decodes_as_utf8_plaintext(self):
        text = read_fixture('sample.txt').decode('utf-8')
        self.assertGreater(len(text.strip()), 0)


if __name__ == '__main__':
    unittest.main()
