import unittest

from omegaconf import OmegaConf
from omegaconf.errors import OmegaConfBaseException

from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import (
    CandidateSelectionService,
)
from doc_to_markdown_core_lib.data_layers.service.document_service import (
    DocumentService,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.tesseract_extractor import (
    TesseractExtractor,
)
from doc_to_markdown_core_lib.doc_to_markdown_core_lib import DocToMarkdownCoreLib


class TestDocToMarkdownCoreLib(unittest.TestCase):
    def test_full_config_wires_document_service(self):
        config = OmegaConf.create({
            'core_lib': {
                'extraction': {
                    'ocr_languages': ['eng', 'heb'],
                    'confidence_threshold': 0.9,
                }
            }
        })
        lib = DocToMarkdownCoreLib(config)
        # Selection service is an implementation detail — callers only
        # see ``lib.document``. We still reach in here to assert wiring.
        self.assertIsInstance(lib.document, DocumentService)
        self.assertIsInstance(
            lib.document._selection_service, CandidateSelectionService
        )
        self.assertEqual(
            lib.document._selection_service._confidence_threshold, 0.9
        )
        self.assertEqual(self._tesseract_languages(lib), ['eng', 'heb'])

    def test_missing_extraction_section_fails_loud(self):
        # No defensive fallback: a config without the extraction section
        # must raise at construction, not silently default.
        config = OmegaConf.create({'core_lib': {}})
        with self.assertRaises(OmegaConfBaseException):
            DocToMarkdownCoreLib(config)

    def test_partial_extraction_config_fails_loud(self):
        # extraction present but missing a required key -> still fails.
        config = OmegaConf.create({
            'core_lib': {'extraction': {'ocr_languages': ['eng']}}
        })
        with self.assertRaises(OmegaConfBaseException):
            DocToMarkdownCoreLib(config)

    @staticmethod
    def _tesseract_languages(lib):
        tesseract_extractors = [
            extractor
            for extractor in lib.document._extractors
            if isinstance(extractor, TesseractExtractor)
        ]
        return tesseract_extractors[0]._languages


if __name__ == '__main__':
    unittest.main()
