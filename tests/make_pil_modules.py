import types
from unittest import mock


def make_pil_modules(open_returns=None):
    """Fake ``PIL`` + ``PIL.Image`` module pair."""
    pil_module = types.ModuleType('PIL')
    image_module = types.ModuleType('PIL.Image')

    class FakeImage:
        def __init__(self, name='img'):
            self.name = name

    image_module.open = mock.Mock(return_value=open_returns or FakeImage())
    pil_module.Image = image_module
    return pil_module, image_module
