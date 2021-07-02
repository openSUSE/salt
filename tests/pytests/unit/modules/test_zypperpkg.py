import pytest
import salt.modules.pkg_resource as pkg_resource
import salt.modules.zypperpkg as zypper
from tests.support.mock import MagicMock, patch


@pytest.fixture
def configure_loader_modules():
    return {zypper: {"rpm": None}, pkg_resource: {}}


def test_pkg_hold():
    """
    Tests holding packages with Zypper
    """

    # Test openSUSE 15.3
    list_locks_mock = {
        "bar": {"type": "package", "match_type": "glob", "case_sensitive": "on"},
        "minimal_base": {
            "type": "pattern",
            "match_type": "glob",
            "case_sensitive": "on",
        },
        "baz": {"type": "package", "match_type": "glob", "case_sensitive": "on"},
    }

    cmd = MagicMock(
        return_value={
            "pid": 1234,
            "retcode": 0,
            "stdout": "Specified lock has been successfully added.",
            "stderr": "",
        }
    )
    with patch.object(
        zypper, "list_locks", MagicMock(return_value=list_locks_mock)
    ), patch.dict(zypper.__salt__, {"cmd.run_all": cmd}):
        ret = zypper.hold("foo")
        assert ret["foo"]["changes"]["old"] == ""
        assert ret["foo"]["changes"]["new"] == "hold"
        assert ret["foo"]["comment"] == "Package foo is now being held."
        cmd.assert_called_once_with(
            ["zypper", "--non-interactive", "--no-refresh", "al", "foo"],
            env={},
            output_loglevel="trace",
            python_shell=False,
        )
        cmd.reset_mock()
        ret = zypper.hold(pkgs=["foo", "bar"])
        assert ret["foo"]["changes"]["old"] == ""
        assert ret["foo"]["changes"]["new"] == "hold"
        assert ret["foo"]["comment"] == "Package foo is now being held."
        assert ret["bar"]["changes"] == {}
        assert ret["bar"]["comment"] == "Package bar is already set to be held."
        cmd.assert_called_once_with(
            ["zypper", "--non-interactive", "--no-refresh", "al", "foo"],
            env={},
            output_loglevel="trace",
            python_shell=False,
        )


def test_pkg_unhold():
    """
    Tests unholding packages with Zypper
    """

    # Test openSUSE 15.3
    list_locks_mock = {
        "bar": {"type": "package", "match_type": "glob", "case_sensitive": "on"},
        "minimal_base": {
            "type": "pattern",
            "match_type": "glob",
            "case_sensitive": "on",
        },
        "baz": {"type": "package", "match_type": "glob", "case_sensitive": "on"},
    }

    cmd = MagicMock(
        return_value={
            "pid": 1234,
            "retcode": 0,
            "stdout": "1 lock has been successfully removed.",
            "stderr": "",
        }
    )
    with patch.object(
        zypper, "list_locks", MagicMock(return_value=list_locks_mock)
    ), patch.dict(zypper.__salt__, {"cmd.run_all": cmd}):
        ret = zypper.unhold("foo")
        assert ret["foo"]["comment"] == "Package foo was already unheld."
        cmd.assert_not_called()
        cmd.reset_mock()
        ret = zypper.unhold(pkgs=["foo", "bar"])
        assert ret["foo"]["changes"] == {}
        assert ret["foo"]["comment"] == "Package foo was already unheld."
        assert ret["bar"]["changes"]["old"] == "hold"
        assert ret["bar"]["changes"]["new"] == ""
        assert ret["bar"]["comment"] == "Package bar is no longer held."
        cmd.assert_called_once_with(
            ["zypper", "--non-interactive", "--no-refresh", "rl", "bar"],
            env={},
            output_loglevel="trace",
            python_shell=False,
        )


def test_pkg_list_holds():
    """
    Tests listing of calculated held packages with Zypper
    """

    # Test openSUSE 15.3
    list_locks_mock = {
        "bar": {"type": "package", "match_type": "glob", "case_sensitive": "on"},
        "minimal_base": {
            "type": "pattern",
            "match_type": "glob",
            "case_sensitive": "on",
        },
        "baz": {"type": "package", "match_type": "glob", "case_sensitive": "on"},
    }
    installed_pkgs = {
        "foo": [{"edition": "1.2.3-1.1"}],
        "bar": [{"edition": "2.3.4-2.1", "epoch": "2"}],
    }

    def zypper_search_mock(name, *_args, **_kwargs):
        if name in installed_pkgs:
            return {name: installed_pkgs.get(name)}

    with patch.object(
        zypper, "list_locks", MagicMock(return_value=list_locks_mock)
    ), patch.object(
        zypper, "search", MagicMock(side_effect=zypper_search_mock)
    ), patch.object(
        zypper, "info_installed", MagicMock(side_effect=zypper_search_mock)
    ):
        ret = zypper.list_holds()
        assert len(ret) == 1
        assert "bar-2:2.3.4-2.1.*" in ret
