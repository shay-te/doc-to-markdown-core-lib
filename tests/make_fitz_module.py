import types


def make_fitz_module(pages_text=None, open_raises=None, pixmap_bytes=None):
    """Fake PyMuPDF: pages expose text and PNG pixmaps."""
    fitz_module = types.ModuleType('fitz')
    pages_text = pages_text if pages_text is not None else ['hello world']
    pixmap_bytes = pixmap_bytes or b'\x89PNG\r\n\x1a\n' + b'\x00' * 16

    class FakePixmap:
        def tobytes(self, image_format):
            return pixmap_bytes

    class FakePage:
        def __init__(self, text):
            self._text = text

        def get_text(self, mode='text'):
            return self._text

        def get_pixmap(self, dpi=200):
            return FakePixmap()

    class FakeDoc:
        def __init__(self):
            self._pages = [FakePage(text) for text in pages_text]

        def __iter__(self):
            return iter(self._pages)

        def __len__(self):
            return len(self._pages)

        def close(self):
            pass

    def fake_open(stream=None, filetype=None):
        if open_raises is not None:
            raise open_raises
        return FakeDoc()

    fitz_module.open = fake_open
    return fitz_module
