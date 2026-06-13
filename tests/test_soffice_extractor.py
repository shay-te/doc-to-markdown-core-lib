import os
import subprocess
import sys
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.doc.soffice_extractor import (
    SofficeExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType
from tests.make_mammoth_module import make_mammoth_module
from tests.patch_module import patch_module

_SOFFICE_MODULE = (
    'doc_to_markdown_core_lib.data_layers.service.extractors.doc.soffice_extractor'
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
        ), patch_module('mammoth', make_mammoth_module('# converted heading')):
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


if __name__ == '__main__':
    unittest.main()
