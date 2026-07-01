import os
import subprocess
import unittest
from unittest import mock

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.doc.antiword_extractor import (
    AntiwordExtractor,
    _PLAIN_TEXT_CONFIDENCE_DISCOUNT,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType

_ANTIWORD_MODULE = (
    'doc_to_markdown_core_lib.data_layers.service.extractors.doc.antiword_extractor'
)


class TestAntiwordExtractor(unittest.TestCase):
    def test_unavailable_without_binary(self):
        with mock.patch(f'{_ANTIWORD_MODULE}.shutil.which', return_value=None):
            with self.assertRaises(ExtractorUnavailable):
                AntiwordExtractor().extract(b'\xd0\xcf', FileType.DOC)

    def test_run_failure_raises_unavailable(self):
        def failing_run(command, **kwargs):
            raise subprocess.CalledProcessError(returncode=1, cmd=command)

        with mock.patch(
            f'{_ANTIWORD_MODULE}.shutil.which', return_value='/usr/bin/antiword'
        ), mock.patch(
            f'{_ANTIWORD_MODULE}.subprocess.run', side_effect=failing_run
        ):
            with self.assertRaises(ExtractorUnavailable):
                AntiwordExtractor().extract(b'\xd0\xcf', FileType.DOC)

    def test_happy_path_decodes_stdout_and_cleans_up(self):
        completed = mock.Mock(stdout=b'legacy doc body')
        with mock.patch(
            f'{_ANTIWORD_MODULE}.shutil.which', return_value='/usr/bin/antiword'
        ), mock.patch(
            f'{_ANTIWORD_MODULE}.subprocess.run', return_value=completed
        ) as run_mock:
            result = AntiwordExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertEqual(result.markdown, 'legacy doc body')
        self.assertGreater(result.confidence, 0.0)
        # the .doc temp file handed to antiword must be cleaned up afterwards
        temp_path = run_mock.call_args.args[0][1]
        self.assertTrue(temp_path.endswith(f'.{FileType.DOC.value}'))
        self.assertFalse(os.path.exists(temp_path))

    def test_full_length_text_caps_at_discounted_confidence(self):
        completed = mock.Mock(stdout=('word ' * 1000).encode('utf-8'))
        with mock.patch(
            f'{_ANTIWORD_MODULE}.shutil.which', return_value='/usr/bin/antiword'
        ), mock.patch(
            f'{_ANTIWORD_MODULE}.subprocess.run', return_value=completed
        ):
            result = AntiwordExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertAlmostEqual(result.confidence, _PLAIN_TEXT_CONFIDENCE_DISCOUNT)

    def test_unlink_oserror_is_swallowed(self):
        completed = mock.Mock(stdout=b'still ok')
        with mock.patch(
            f'{_ANTIWORD_MODULE}.shutil.which', return_value='/usr/bin/antiword'
        ), mock.patch(
            f'{_ANTIWORD_MODULE}.subprocess.run', return_value=completed
        ), mock.patch(
            f'{_ANTIWORD_MODULE}.os.unlink', side_effect=OSError('locked')
        ):
            result = AntiwordExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertEqual(result.markdown, 'still ok')


if __name__ == '__main__':
    unittest.main()
