from core_lib.web_helpers.web_helprs_utils import WebHelpersUtils
# doc_to_markdown_core_lib_import


class DocToMarkdownCoreLibInstance(object):
    _app_instance = None

    @staticmethod
    def init(core_lib_cfg):
        if not DocToMarkdownCoreLibInstance._app_instance:
            # WebHelpersUtils.init(WebHelpersUtils.ServerType.FLASK) #TODO: initilazie the correct server type
            DocToMarkdownCoreLibInstance._app_instance = DocToMarkdownCoreLibClass(core_lib_cfg)

    @staticmethod
    def get() -> DocToMarkdownCoreLibClass:
        return DocToMarkdownCoreLibInstance._app_instance