import subprocess
import unittest
from unittest import mock

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.doc.wvtext_extractor import (
    WvTextExtractor,
    _PLAIN_TEXT_CONFIDENCE_DISCOUNT,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType

_WVTEXT_MODULE = (
    'doc_to_markdown_core_lib.data_layers.service.extractors.doc.wvtext_extractor'
)


def _writing_run(output_text):
    # ``wvText <input> <output>`` — the third arg is the output path.
    def run(command, **kwargs):
        with open(command[2], 'w', encoding='utf-8') as output_file:
            output_file.write(output_text)

    return run


class TestWvTextExtractor(unittest.TestCase):
    def test_unavailable_without_binary(self):
        with mock.patch(f'{_WVTEXT_MODULE}.shutil.which', return_value=None):
            with self.assertRaises(ExtractorUnavailable):
                WvTextExtractor().extract(b'\xd0\xcf', FileType.DOC)

    def test_run_failure_raises_unavailable(self):
        def failing_run(command, **kwargs):
            raise subprocess.CalledProcessError(returncode=1, cmd=command)

        with mock.patch(
            f'{_WVTEXT_MODULE}.shutil.which', return_value='/usr/bin/wvText'
        ), mock.patch(
            f'{_WVTEXT_MODULE}.subprocess.run', side_effect=failing_run
        ):
            with self.assertRaises(ExtractorUnavailable):
                WvTextExtractor().extract(b'\xd0\xcf', FileType.DOC)

    def test_missing_output_raises_unavailable(self):
        with mock.patch(
            f'{_WVTEXT_MODULE}.shutil.which', return_value='/usr/bin/wvText'
        ), mock.patch(
            f'{_WVTEXT_MODULE}.subprocess.run', return_value=None
        ):
            with self.assertRaises(ExtractorUnavailable):
                WvTextExtractor().extract(b'\xd0\xcf', FileType.DOC)

    def test_happy_path_reads_output_file(self):
        with mock.patch(
            f'{_WVTEXT_MODULE}.shutil.which', return_value='/usr/bin/wvText'
        ), mock.patch(
            f'{_WVTEXT_MODULE}.subprocess.run', side_effect=_writing_run('  wv body  ')
        ):
            result = WvTextExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertEqual(result.markdown, 'wv body')
        self.assertGreater(result.confidence, 0.0)

    def test_full_length_text_caps_at_discounted_confidence(self):
        with mock.patch(
            f'{_WVTEXT_MODULE}.shutil.which', return_value='/usr/bin/wvText'
        ), mock.patch(
            f'{_WVTEXT_MODULE}.subprocess.run', side_effect=_writing_run('word ' * 1000)
        ):
            result = WvTextExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertAlmostEqual(result.confidence, _PLAIN_TEXT_CONFIDENCE_DISCOUNT)


if __name__ == '__main__':
    unittest.main()
