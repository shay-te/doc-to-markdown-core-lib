import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.types import FileType
from tests.make_markdown_service import make_markdown_service
from tests.stub_extractor import StubExtractor


class TestMarkdownServiceCleanTierNoPrimaryEntry(unittest.TestCase):
    def test_clean_tier_image_falls_back_to_first_match(self):
        # 'image' isn't in _PRIMARY_PER_TYPE → fall through to matches[:1].
        service = make_markdown_service(
            [
                StubExtractor(
                    'img-a', 'aaa', confidence=0.9, file_types=(FileType.IMAGE.value,)
                ),
                StubExtractor(
                    'img-b', 'bbb', confidence=0.5, file_types=(FileType.IMAGE.value,)
                ),
            ],
        )
        with mock.patch(
            'doc_to_markdown_core_lib.data_layers.service.markdown_service.detect_tier',
            return_value='clean',
        ):
            result = service.extract(b'\x89PNG', FileType.IMAGE.value)
        self.assertEqual(result.markdown, 'aaa')


if __name__ == '__main__':
    unittest.main()
