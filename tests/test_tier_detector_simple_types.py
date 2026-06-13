import unittest

from doc_to_markdown_core_lib.data_layers.service.file_type import FileType
from doc_to_markdown_core_lib.data_layers.service.tier import Tier
from doc_to_markdown_core_lib.data_layers.service.tier_detector import detect_tier


class TestTierDetectorSimpleTypes(unittest.TestCase):
    def test_txt_md_docx_are_clean(self):
        for file_type in (FileType.TXT, FileType.MD, FileType.DOCX):
            self.assertEqual(detect_tier(b'x', file_type), Tier.CLEAN)

    def test_image_is_risky(self):
        self.assertEqual(
            detect_tier(b'\x89PNG\r\n\x1a\n', FileType.IMAGE), Tier.RISKY
        )


if __name__ == '__main__':
    unittest.main()
