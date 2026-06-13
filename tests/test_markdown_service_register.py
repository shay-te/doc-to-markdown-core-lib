import unittest

from doc_to_markdown_core_lib.data_layers.service.file_type import FileType
from tests.make_markdown_service import make_markdown_service
from tests.stub_extractor import StubExtractor


class TestMarkdownServiceRegister(unittest.TestCase):
    def test_register_appends_host_extractor_to_pipeline(self):
        # ``register`` is the public hook for host apps to plug their
        # own engine in without subclassing — the new extractor must
        # become part of the candidate fan-out on the next ``extract``.
        service = make_markdown_service([])
        host_extractor = StubExtractor(
            'host-engine',
            'host markdown',
            confidence=0.99,
            file_types=(FileType.PDF.value,),
        )
        service.register(host_extractor)

        result = service.extract(b'%PDF', FileType.PDF.value)
        self.assertEqual(result.markdown, 'host markdown')


if __name__ == '__main__':
    unittest.main()
