import unittest

from doc_to_markdown_core_lib.data_layers.service.extractor import Extractor


class TestExtractorAbstract(unittest.TestCase):
    def test_cannot_instantiate_directly(self):
        with self.assertRaises(TypeError):
            Extractor()  # type: ignore[abstract]


if __name__ == '__main__':
    unittest.main()
