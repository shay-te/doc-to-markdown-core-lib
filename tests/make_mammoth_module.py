import types


def make_mammoth_module(text):
    """Fake ``mammoth`` whose ``convert_to_markdown`` returns ``text``."""
    mammoth_module = types.ModuleType('mammoth')

    class Result:
        def __init__(self, value):
            self.value = value

    mammoth_module.convert_to_markdown = lambda file_object: Result(text)
    return mammoth_module
