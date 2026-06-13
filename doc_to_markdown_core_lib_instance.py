from doc_to_markdown_core_lib.doc_to_markdown_core_lib import DocToMarkdownCoreLib


class DocToMarkdownCoreLibInstance(object):
    _app_instance = None

    @staticmethod
    def init(core_lib_cfg):
        if not DocToMarkdownCoreLibInstance._app_instance:
            DocToMarkdownCoreLibInstance._app_instance = DocToMarkdownCoreLib(core_lib_cfg)

    @staticmethod
    def get() -> DocToMarkdownCoreLib:
        return DocToMarkdownCoreLibInstance._app_instance
