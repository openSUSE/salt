import sys

import pytest


@pytest.fixture(scope="package", autouse=True)
def _auto_skip_on_salt_bundle():
    if "venv-salt-minion" in sys.executable:
        pytest.skip("Skipping for Salt Bundle (tests are not compatible)")
