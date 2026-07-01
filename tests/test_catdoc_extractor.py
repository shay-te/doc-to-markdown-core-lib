import os
import subprocess
import unittest
from unittest import mock

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.doc.catdoc_extractor import (
    CatdocExtractor,
    _PLAIN_TEXT_CONFIDENCE_DISCOUNT,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType

_CATDOC_MODULE = (
    'doc_to_markdown_core_lib.data_layers.service.extractors.doc.catdoc_extractor'
)


class TestCatdocExtractor(unittest.TestCase):
    def test_unavailable_without_binary(self):
        with mock.patch(f'{_CATDOC_MODULE}.shutil.which', return_value=None):
            with self.assertRaises(ExtractorUnavailable):
                CatdocExtractor().extract(b'\xd0\xcf', FileType.DOC)

    def test_run_timeout_raises_unavailable(self):
        def timing_out_run(command, **kwargs):
            raise subprocess.TimeoutExpired(cmd=command, timeout=1)

        with mock.patch(
            f'{_CATDOC_MODULE}.shutil.which', return_value='/usr/bin/catdoc'
        ), mock.patch(
            f'{_CATDOC_MODULE}.subprocess.run', side_effect=timing_out_run
        ):
            with self.assertRaises(ExtractorUnavailable):
                CatdocExtractor().extract(b'\xd0\xcf', FileType.DOC)

    def test_happy_path_decodes_stdout_and_cleans_up(self):
        completed = mock.Mock(stdout=b'catdoc body')
        with mock.patch(
            f'{_CATDOC_MODULE}.shutil.which', return_value='/usr/bin/catdoc'
        ), mock.patch(
            f'{_CATDOC_MODULE}.subprocess.run', return_value=completed
        ) as run_mock:
            result = CatdocExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertEqual(result.markdown, 'catdoc body')
        self.assertGreater(result.confidence, 0.0)
        temp_path = run_mock.call_args.args[0][1]
        self.assertTrue(temp_path.endswith(f'.{FileType.DOC.value}'))
        self.assertFalse(os.path.exists(temp_path))

    def test_full_length_text_caps_at_discounted_confidence(self):
        completed = mock.Mock(stdout=('word ' * 1000).encode('utf-8'))
        with mock.patch(
            f'{_CATDOC_MODULE}.shutil.which', return_value='/usr/bin/catdoc'
        ), mock.patch(
            f'{_CATDOC_MODULE}.subprocess.run', return_value=completed
        ):
            result = CatdocExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertAlmostEqual(result.confidence, _PLAIN_TEXT_CONFIDENCE_DISCOUNT)

    def test_unlink_oserror_is_swallowed(self):
        completed = mock.Mock(stdout=b'still ok')
        with mock.patch(
            f'{_CATDOC_MODULE}.shutil.which', return_value='/usr/bin/catdoc'
        ), mock.patch(
            f'{_CATDOC_MODULE}.subprocess.run', return_value=completed
        ), mock.patch(
            f'{_CATDOC_MODULE}.os.unlink', side_effect=OSError('locked')
        ):
            result = CatdocExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertEqual(result.markdown, 'still ok')


if __name__ == '__main__':
    unittest.main()
