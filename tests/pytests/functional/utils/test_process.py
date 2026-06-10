"""
tests.pytests.functional.utils.test_process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test salt's process utility module
"""
import pytest

import pathlib
import subprocess
import sys

import salt.utils.process


class Process(salt.utils.process.SignalHandlingProcess):
    def run(self):
        pass


@pytest.fixture
def process_manager():
    _process_manager = salt.utils.process.ProcessManager(wait_for_kill=5)
    try:
        yield _process_manager
    finally:
        _process_manager.terminate()


def test_process_manager_60749(process_manager):
    """
    Regression test for issue #60749
    """

    process_manager.add_process(Process)
    process_manager.check_children()


def test_process_preimports_multiprocessing_connection_68573(tmp_path):
    """
    Regression test for issue #68573.

    multiprocessing.popen_fork.Popen.wait() does a lazy
    ``from multiprocessing.connection import wait`` on first use. When a
    second SIGTERM is delivered during the shutdown path that handler
    re-enters salt.utils.process.ProcessManager.kill_children -> join(0),
    which tries the same import while the module is partially
    initialised, producing::

        ImportError: cannot import name 'wait' from partially initialized
        module 'multiprocessing.connection'

    Importing salt.utils.process must therefore eagerly import
    multiprocessing.connection so the module is fully initialised before
    any signal handler can run.

    Must run in a fresh subprocess: in-process pytest pollutes
    sys.modules with multiprocessing.connection long before this test
    runs.
    """
    # Make the subprocess load the same salt package the test imports.
    # Locally, this might be the editable install in the venv; in CI it is
    # the in-tree code. Both cases work because we explicitly prepend the
    # directory containing the salt package to sys.path.
    salt_module = pathlib.Path(salt.utils.process.__file__).resolve()
    code_dir = salt_module.parent.parent.parent
    script = tmp_path / "check_preimport.py"
    script.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(code_dir)!r})\n"
        "assert 'multiprocessing.connection' not in sys.modules, (\n"
        "    'precondition failed: multiprocessing.connection already imported'\n"
        ")\n"
        "import salt.utils.process  # noqa: F401\n"
        "assert 'multiprocessing.connection' in sys.modules, (\n"
        "    'salt.utils.process must pre-import multiprocessing.connection '\n"
        "    'to avoid a partially-initialised-module ImportError when a '\n"
        "    'reentrant SIGTERM hits Process.join(0); see issue #68573'\n"
        ")\n"
    )
    result = subprocess.run(
        [sys.executable, str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
        cwd=str(tmp_path),
    )
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
