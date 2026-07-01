import unittest

from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import (
    MERGE_EXTRACTOR_NAME,
    _best_page_version,
    _merge_pages,
    _split_pages,
)


def _paged(*texts):
    return '\n\n'.join(
        f'<!-- page {number} -->\n\n{text}'
        for number, text in enumerate(texts, start=1)
    )


class TestPerPageMerge(unittest.TestCase):
    def test_split_pages_none_without_markers(self):
        self.assertIsNone(_split_pages('plain text, no page markers'))

    def test_split_pages_extracts_each_page_including_last(self):
        self.assertEqual(
            _split_pages(_paged('alpha', 'beta gamma')),
            {1: 'alpha', 2: 'beta gamma'},
        )

    def test_best_page_version_single(self):
        self.assertEqual(_best_page_version(['only version']), 'only version')

    def test_best_page_version_prefers_corroborated_over_noise(self):
        # Two extractors agree; one is noise → the agreed text wins.
        best = _best_page_version(
            ['shared body text', 'shared body text', 'zzz qqq noise']
        )
        self.assertEqual(best, 'shared body text')

    def test_merge_none_with_fewer_than_two_paged_candidates(self):
        candidates = [
            ExtractionCandidate('pymupdf', _paged('a', 'b')),
            ExtractionCandidate('markitdown', 'whole doc, no markers'),
        ]
        self.assertIsNone(_merge_pages(candidates))

    def test_merge_assembles_best_of_each_page(self):
        # Page 1: text extractors agree. Page 2: only OCR has content (image).
        text_a = ExtractionCandidate('pymupdf', _paged('real body text', ''))
        text_b = ExtractionCandidate('pdfplumber', _paged('real body text', ''))
        ocr = ExtractionCandidate(
            'rapidocr', _paged('reel bady text', 'SCANNED NEWSPAPER WORDS')
        )
        merged = _merge_pages([text_a, text_b, ocr])
        self.assertEqual(merged.extractor, MERGE_EXTRACTOR_NAME)
        pages = _split_pages(merged.markdown)
        self.assertEqual(pages[1], 'real body text')  # corroborated text wins
        self.assertEqual(pages[2], 'SCANNED NEWSPAPER WORDS')  # only OCR had it

    def test_merge_unions_pages_present_in_only_some_candidates(self):
        # One extractor saw a 3rd page the others didn't — it still appears.
        short = ExtractionCandidate('pymupdf', _paged('one', 'two'))
        long = ExtractionCandidate('pdfplumber', _paged('one', 'two', 'three'))
        pages = _split_pages(_merge_pages([short, long]).markdown)
        self.assertEqual(pages[3], 'three')


if __name__ == '__main__':
    unittest.main()
