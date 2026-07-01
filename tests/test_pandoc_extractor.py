import os
import subprocess
import unittest
from unittest import mock

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.docx.pandoc_extractor import (
    PandocExtractor,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType

_PANDOC_MODULE = (
    'doc_to_markdown_core_lib.data_layers.service.extractors.docx.pandoc_extractor'
)


class TestPandocExtractor(unittest.TestCase):
    def test_unavailable_without_binary(self):
        with mock.patch(f'{_PANDOC_MODULE}.shutil.which', return_value=None):
            with self.assertRaises(ExtractorUnavailable):
                PandocExtractor().extract(b'PK\x03\x04', FileType.DOCX)

    def test_run_failure_raises_unavailable(self):
        def failing_run(command, **kwargs):
            raise subprocess.CalledProcessError(returncode=1, cmd=command)

        with mock.patch(
            f'{_PANDOC_MODULE}.shutil.which', return_value='/usr/bin/pandoc'
        ), mock.patch(
            f'{_PANDOC_MODULE}.subprocess.run', side_effect=failing_run
        ):
            with self.assertRaises(ExtractorUnavailable):
                PandocExtractor().extract(b'PK\x03\x04', FileType.DOCX)

    def test_happy_path_converts_to_gfm_and_cleans_up(self):
        completed = mock.Mock(stdout=b'# Heading\n\n- bullet')
        with mock.patch(
            f'{_PANDOC_MODULE}.shutil.which', return_value='/usr/bin/pandoc'
        ), mock.patch(
            f'{_PANDOC_MODULE}.subprocess.run', return_value=completed
        ) as run_mock:
            result = PandocExtractor().extract(b'PK\x03\x04', FileType.DOCX)
        self.assertEqual(result.markdown, '# Heading\n\n- bullet')
        self.assertGreater(result.confidence, 0.0)
        command = run_mock.call_args.args[0]
        self.assertIn('gfm', command)
        temp_path = command[1]
        self.assertTrue(temp_path.endswith(f'.{FileType.DOCX.value}'))
        self.assertFalse(os.path.exists(temp_path))

    def test_full_length_markdown_caps_at_full_confidence(self):
        # Structured Markdown carries no plain-text discount, so a long
        # document saturates at 1.0.
        completed = mock.Mock(stdout=('word ' * 1000).encode('utf-8'))
        with mock.patch(
            f'{_PANDOC_MODULE}.shutil.which', return_value='/usr/bin/pandoc'
        ), mock.patch(
            f'{_PANDOC_MODULE}.subprocess.run', return_value=completed
        ):
            result = PandocExtractor().extract(b'PK\x03\x04', FileType.DOCX)
        self.assertAlmostEqual(result.confidence, 1.0)

    def test_unlink_oserror_is_swallowed(self):
        completed = mock.Mock(stdout=b'still ok')
        with mock.patch(
            f'{_PANDOC_MODULE}.shutil.which', return_value='/usr/bin/pandoc'
        ), mock.patch(
            f'{_PANDOC_MODULE}.subprocess.run', return_value=completed
        ), mock.patch(
            f'{_PANDOC_MODULE}.os.unlink', side_effect=OSError('locked')
        ):
            result = PandocExtractor().extract(b'PK\x03\x04', FileType.DOCX)
        self.assertEqual(result.markdown, 'still ok')


if __name__ == '__main__':
    unittest.main()
