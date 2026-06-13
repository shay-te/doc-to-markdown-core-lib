import sys
from unittest import mock


def patch_module(module_name, module):
    """Installs ``module`` under ``module_name`` for the ``with`` scope."""
    return mock.patch.dict(sys.modules, {module_name: module})
