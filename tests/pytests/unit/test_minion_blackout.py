"""
Unit tests for the SLS aware blackout whitelist in salt.minion
"""

import pytest

import salt.minion
from salt.exceptions import SaltInvocationError

ALLOWED = ["packages.profileupdate"]


@pytest.mark.parametrize(
    "fun,args,kwargs,expected",
    [
        ("state.apply", ["packages.profileupdate"], {}, True),
        ("state.apply", [], {"mods": "packages.profileupdate"}, True),
        ("state.sls", [], {"mods": ["packages.profileupdate"]}, True),
        ("state.apply", ["packages.profileupdate, other"], {}, False),
        ("state.apply", [["packages.profileupdate", "other"]], {}, False),
        ("state.apply", ["other"], {}, False),
        ("state.apply", [], {}, False),
        ("state.apply", [""], {}, False),
        ("test.ping", [], {}, True),
    ],
)
def test_blackout_state_allowed(fun, args, kwargs, expected):
    assert salt.minion._blackout_state_allowed(fun, args, kwargs, ALLOWED) is expected


def _minion(pillar=None, grains=None):
    minion = salt.minion.Minion.__new__(salt.minion.Minion)
    minion.connected = True
    minion.opts = {"pillar": pillar or {}, "grains": grains or {}}
    return minion


@pytest.mark.parametrize("source", ["pillar", "grains"])
def test_execute_job_function_state_whitelist(source):
    conf = {
        "minion_blackout": True,
        "minion_blackout_whitelist": ["state.apply"],
        "minion_blackout_state_whitelist": ALLOWED,
    }
    minion = _minion(**{source: conf})
    minion.functions = {}
    with pytest.raises(SaltInvocationError, match="blackout"):
        minion._execute_job_function("state.apply", ["other"], "direct_call", {}, {})
    with pytest.raises(SaltInvocationError, match="blackout"):
        minion._execute_job_function("state.apply", [], "direct_call", {}, {})
    with pytest.raises(SaltInvocationError, match="blackout"):
        minion._execute_job_function("pkg.install", ["foo"], "direct_call", {}, {})


def test_execute_job_function_without_state_whitelist_is_unchanged():
    minion = _minion(
        pillar={
            "minion_blackout": True,
            "minion_blackout_whitelist": ["state.apply"],
        }
    )
    minion.functions = {}
    # No blackout error: it gets past the check and fails later on the executors
    with pytest.raises(SaltInvocationError, match="Wrong executors"):
        minion._execute_job_function("state.apply", ["other"], None, {}, {})
