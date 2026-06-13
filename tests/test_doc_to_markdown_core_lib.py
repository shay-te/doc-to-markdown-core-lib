import unittest

from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import (
    CandidateSelectionService,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.tesseract_extractor import (
    TesseractExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.markdown_service import (
    MarkdownService,
)
from doc_to_markdown_core_lib.doc_to_markdown_core_lib import DocToMarkdownCoreLib


class TestDocToMarkdownCoreLib(unittest.TestCase):
    def test_full_config_wires_services(self):
        config = {
            'core_lib': {
                'extraction': {
                    'ocr_languages': ['eng', 'heb'],
                    'confidence_threshold': 0.9,
                }
            }
        }
        lib = DocToMarkdownCoreLib(config)
        self.assertIsInstance(lib.selection, CandidateSelectionService)
        self.assertIsInstance(lib.markdown, MarkdownService)
        self.assertIs(lib.markdown._selection_service, lib.selection)
        self.assertEqual(lib.selection._confidence_threshold, 0.9)
        self.assertEqual(self._tesseract_languages(lib), ['eng', 'heb'])

    def test_defaults_when_extraction_config_missing(self):
        lib = DocToMarkdownCoreLib({'core_lib': {}})
        self.assertEqual(lib.selection._confidence_threshold, 0.8)
        self.assertEqual(
            self._tesseract_languages(lib),
            list(MarkdownService.DEFAULT_OCR_LANGUAGES),
        )

    def test_none_extraction_section_uses_defaults(self):
        lib = DocToMarkdownCoreLib({'core_lib': {'extraction': None}})
        self.assertEqual(lib.selection._confidence_threshold, 0.8)
        self.assertEqual(
            self._tesseract_languages(lib),
            list(MarkdownService.DEFAULT_OCR_LANGUAGES),
        )

    def test_none_config_uses_defaults(self):
        lib = DocToMarkdownCoreLib(None)
        self.assertEqual(lib.selection._confidence_threshold, 0.8)
        self.assertEqual(
            self._tesseract_languages(lib),
            list(MarkdownService.DEFAULT_OCR_LANGUAGES),
        )

    @staticmethod
    def _tesseract_languages(lib):
        tesseract_extractors = [
            extractor
            for extractor in lib.markdown._extractors
            if isinstance(extractor, TesseractExtractor)
        ]
        return tesseract_extractors[0]._languages


if __name__ == '__main__':
    unittest.main()
