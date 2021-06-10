"""
Unit test for venv executor
"""

import pytest

import os

import salt.executors.venv as venv_exec


@pytest.fixture(scope="session", autouse=True)
def executors():
    env_save = dict(os.environ)
    venv_exec.__executors__ = {"direct_call.execute": direct_call_helper}
    yield
    os.environ.clear()
    os.environ.update(env_save)


def direct_call_helper(_opts, _data, _func, _args, _kwargs):
    return


def test_wipe_PYTHONHOME_environment_variable_for_venvjailed_minion(executors):
    """
    In case of using salt-minion in the venvjailed environment
    PYTHONHOME environment variable should be wiped
    """
    os.environ["PYTHONHOME"] = os.environ["VIRTUAL_ENV"] = "/opt/venv-salt-minion"
    venv_exec.execute(None, None, None, None, None)
    assert "PYTHONHOME" not in os.environ


def test_no_wipe_PYTHONHOME_environment_variable_for_non_venvjailed_minion(executors):
    """
    In case of using salt-minion in the non venvjailed environment
    PYTHONHOME environment variable shouldn't be changed
    """
    test_path = "/usr"
    os.environ["PYTHONHOME"] = test_path
    venv_exec.execute(None, None, None, None, None)
    assert os.environ["PYTHONHOME"] == test_path
