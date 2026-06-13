import unittest

from doc_to_markdown_core_lib.data_layers.service.file_type import FileType
from doc_to_markdown_core_lib.data_layers.service.tier_detector import detect_tier


class TestTierDetectorSimpleTypes(unittest.TestCase):
    def test_txt_md_docx_are_clean(self):
        # The uppercase variants are deliberately raw strings — they
        # probe the lower() normalization inside detect_tier.
        for file_type in (
            FileType.TXT.value,
            FileType.MD.value,
            FileType.DOCX.value,
            'TXT',
            'MD',
            'DocX',
        ):
            self.assertEqual(detect_tier(b'x', file_type), 'clean')

    def test_image_is_risky(self):
        self.assertEqual(
            detect_tier(b'\x89PNG\r\n\x1a\n', FileType.IMAGE.value), 'risky'
        )

    def test_unknown_type_is_risky(self):
        self.assertEqual(detect_tier(b'x', 'unknown'), 'risky')

    def test_empty_type_is_risky(self):
        self.assertEqual(detect_tier(b'x', ''), 'risky')

    def test_none_type_is_risky(self):
        self.assertEqual(detect_tier(b'x', None), 'risky')


if __name__ == '__main__':
    unittest.main()
