import os

_FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'data')


def read_fixture(name: str) -> bytes:
    """Load a binary fixture from ``tests/data/``.

    Backends remain stubbed in the test suite; these fixtures give the
    byte-level inputs realistic shapes so a future engine-installed
    integration test can reuse them without re-generating data."""
    with open(os.path.join(_FIXTURE_DIR, name), 'rb') as handle:
        return handle.read()
