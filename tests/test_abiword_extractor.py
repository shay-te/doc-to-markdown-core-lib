import subprocess
import unittest
from unittest import mock

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.doc.abiword_extractor import (
    AbiwordExtractor,
    _PLAIN_TEXT_CONFIDENCE_DISCOUNT,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType

_ABIWORD_MODULE = (
    'doc_to_markdown_core_lib.data_layers.service.extractors.doc.abiword_extractor'
)


def _writing_run(output_text):
    # ``abiword --to=txt --to-name=<output> <input>`` — pull the output path
    # out of the ``--to-name=`` flag.
    def run(command, **kwargs):
        output_path = next(
            arg.split('=', 1)[1] for arg in command if arg.startswith('--to-name=')
        )
        with open(output_path, 'w', encoding='utf-8') as output_file:
            output_file.write(output_text)

    return run


class TestAbiwordExtractor(unittest.TestCase):
    def test_unavailable_without_binary(self):
        with mock.patch(f'{_ABIWORD_MODULE}.shutil.which', return_value=None):
            with self.assertRaises(ExtractorUnavailable):
                AbiwordExtractor().extract(b'\xd0\xcf', FileType.DOC)

    def test_run_failure_raises_unavailable(self):
        def failing_run(command, **kwargs):
            raise subprocess.TimeoutExpired(cmd=command, timeout=1)

        with mock.patch(
            f'{_ABIWORD_MODULE}.shutil.which', return_value='/usr/bin/abiword'
        ), mock.patch(
            f'{_ABIWORD_MODULE}.subprocess.run', side_effect=failing_run
        ):
            with self.assertRaises(ExtractorUnavailable):
                AbiwordExtractor().extract(b'\xd0\xcf', FileType.DOC)

    def test_missing_output_raises_unavailable(self):
        with mock.patch(
            f'{_ABIWORD_MODULE}.shutil.which', return_value='/usr/bin/abiword'
        ), mock.patch(
            f'{_ABIWORD_MODULE}.subprocess.run', return_value=None
        ):
            with self.assertRaises(ExtractorUnavailable):
                AbiwordExtractor().extract(b'\xd0\xcf', FileType.DOC)

    def test_happy_path_doc_reads_output_file(self):
        with mock.patch(
            f'{_ABIWORD_MODULE}.shutil.which', return_value='/usr/bin/abiword'
        ), mock.patch(
            f'{_ABIWORD_MODULE}.subprocess.run', side_effect=_writing_run('  abi body  ')
        ):
            result = AbiwordExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertEqual(result.markdown, 'abi body')
        self.assertGreater(result.confidence, 0.0)

    def test_docx_is_supported_too(self):
        with mock.patch(
            f'{_ABIWORD_MODULE}.shutil.which', return_value='/usr/bin/abiword'
        ), mock.patch(
            f'{_ABIWORD_MODULE}.subprocess.run', side_effect=_writing_run('docx body')
        ):
            result = AbiwordExtractor().extract(b'PK\x03\x04', FileType.DOCX)
        self.assertEqual(result.markdown, 'docx body')

    def test_full_length_text_caps_at_discounted_confidence(self):
        with mock.patch(
            f'{_ABIWORD_MODULE}.shutil.which', return_value='/usr/bin/abiword'
        ), mock.patch(
            f'{_ABIWORD_MODULE}.subprocess.run', side_effect=_writing_run('word ' * 1000)
        ):
            result = AbiwordExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertAlmostEqual(result.confidence, _PLAIN_TEXT_CONFIDENCE_DISCOUNT)


if __name__ == '__main__':
    unittest.main()
