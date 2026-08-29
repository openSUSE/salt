import logging
import sys

import pytest

from tests.support.case import ModuleCase, ShellCase

log = logging.getLogger(__name__)


class ExecutorTest(ModuleCase, ShellCase):
    def setup(self):
        self.run_function("saltutil.sync_all")

    @pytest.mark.slow_test
    @pytest.mark.skipif(
        sys.version_info.minor == 11 and "venv-salt-minion" not in sys.executable,
        reason="Flaky with Python 3.11",
    )
    def test_executor(self):
        """
        test that dunders are set
        """
        data = self.run_call("test.arg --module-executors=arg")
        self.assertIn("test.arg fired", "".join(data))

    @pytest.mark.slow_test
    def test_executor_with_multijob(self):
        """
        test that executor is fired when sending a multifunction job
        """
        data = self.run_salt("'*' test.arg,test.arg foo,bar --module-executors=arg")
        self.assertIn("test.arg fired", "".join(data))
