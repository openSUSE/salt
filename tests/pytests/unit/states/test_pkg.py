import pytest
import salt.modules.pkg_resource as pkg_resource
import salt.modules.yumpkg as yumpkg
import salt.states.pkg as pkg
from tests.support.mock import MagicMock, patch


@pytest.fixture
def configure_loader_modules():
    return {
        pkg: {
            "__env__": "base",
            "__salt__": {},
            "__grains__": {"os": "CentOS", "os_family": "RedHat"},
            "__opts__": {"test": False, "cachedir": ""},
            "__instance_id__": "",
            "__low__": {},
            "__utils__": {},
        },
        pkg_resource: {
            "__salt__": {},
            "__grains__": {"os": "CentOS", "os_family": "RedHat"},
        },
        yumpkg: {
            "__salt__": {},
            "__grains__": {
                "os": "CentOS",
                "osarch": "x86_64",
                "osmajorrelease": 7,
            },
            "__opts__": {},
        },
    }


@pytest.mark.parametrize(
    "package_manager", [("Zypper"), ("YUM/DNF"), ("APT")],
)
def test_held_unheld(package_manager):
    """
    Test pkg.held and pkg.unheld with Zypper, YUM/DNF and APT
    """

    if package_manager == "Zypper":
        list_holds_func = "pkg.list_locks"
        list_holds_mock = MagicMock(
            return_value={
                "bar": {
                    "type": "package",
                    "match_type": "glob",
                    "case_sensitive": "on",
                },
                "minimal_base": {
                    "type": "pattern",
                    "match_type": "glob",
                    "case_sensitive": "on",
                },
                "baz": {
                    "type": "package",
                    "match_type": "glob",
                    "case_sensitive": "on",
                },
            }
        )
    elif package_manager == "YUM/DNF":
        list_holds_func = "pkg.list_holds"
        list_holds_mock = MagicMock(
            return_value=["bar-0:1.2.3-1.1.*", "baz-0:2.3.4-2.1.*"]
        )
    elif package_manager == "APT":
        list_holds_func = "pkg.get_selections"
        list_holds_mock = MagicMock(return_value={"hold": ["bar", "baz"]})

    def pkg_hold(name, pkgs=None, *_args, **__kwargs):
        if name and pkgs is None:
            pkgs = [name]
        ret = {}
        for pkg in pkgs:
            ret.update(
                {
                    pkg: {
                        "name": pkg,
                        "changes": {"new": "hold", "old": ""},
                        "result": True,
                        "comment": "Package {} is now being held.".format(pkg),
                    }
                }
            )
        return ret

    def pkg_unhold(name, pkgs=None, *_args, **__kwargs):
        if name and pkgs is None:
            pkgs = [name]
        ret = {}
        for pkg in pkgs:
            ret.update(
                {
                    pkg: {
                        "name": pkg,
                        "changes": {"new": "", "old": "hold"},
                        "result": True,
                        "comment": "Package {} is no longer held.".format(pkg),
                    }
                }
            )
        return ret

    hold_mock = MagicMock(side_effect=pkg_hold)
    unhold_mock = MagicMock(side_effect=pkg_unhold)

    # Testing with Zypper
    with patch.dict(
        pkg.__salt__,
        {
            list_holds_func: list_holds_mock,
            "pkg.hold": hold_mock,
            "pkg.unhold": unhold_mock,
        },
    ):
        # Holding one of two packages
        ret = pkg.held("held-test", pkgs=["foo", "bar"])
        assert "foo" in ret["changes"]
        assert len(ret["changes"]) == 1
        hold_mock.assert_called_once_with(name="held-test", pkgs=["foo"])
        unhold_mock.assert_not_called()

        hold_mock.reset_mock()
        unhold_mock.reset_mock()

        # Holding one of two packages and replacing all the rest held packages
        ret = pkg.held("held-test", pkgs=["foo", "bar"], replace=True)
        assert "foo" in ret["changes"]
        assert "baz" in ret["changes"]
        assert len(ret["changes"]) == 2
        hold_mock.assert_called_once_with(name="held-test", pkgs=["foo"])
        unhold_mock.assert_called_once_with(name="held-test", pkgs=["baz"])

        hold_mock.reset_mock()
        unhold_mock.reset_mock()

        # Remove all holds
        ret = pkg.held("held-test", pkgs=[], replace=True)
        assert "bar" in ret["changes"]
        assert "baz" in ret["changes"]
        assert len(ret["changes"]) == 2
        hold_mock.assert_not_called()
        unhold_mock.assert_any_call(name="held-test", pkgs=["baz"])
        unhold_mock.assert_any_call(name="held-test", pkgs=["bar"])

        hold_mock.reset_mock()
        unhold_mock.reset_mock()

        # Unolding one of two packages
        ret = pkg.unheld("held-test", pkgs=["foo", "bar"])
        assert "bar" in ret["changes"]
        assert len(ret["changes"]) == 1
        unhold_mock.assert_called_once_with(name="held-test", pkgs=["bar"])
        hold_mock.assert_not_called()

        hold_mock.reset_mock()
        unhold_mock.reset_mock()

        # Remove all holds
        ret = pkg.unheld("held-test", all=True)
        assert "bar" in ret["changes"]
        assert "baz" in ret["changes"]
        assert len(ret["changes"]) == 2
        hold_mock.assert_not_called()
        unhold_mock.assert_any_call(name="held-test", pkgs=["baz"])
        unhold_mock.assert_any_call(name="held-test", pkgs=["bar"])


def test_installed_with_single_normalize():
    """
    Test pkg.installed with preventing multiple package name normalisation
    """

    list_no_weird_installed = {
        "pkga": "1.0.1",
        "pkgb": "1.0.2",
        "pkgc": "1.0.3",
    }
    list_no_weird_installed_ver_list = {
        "pkga": ["1.0.1"],
        "pkgb": ["1.0.2"],
        "pkgc": ["1.0.3"],
    }
    list_with_weird_installed = {
        "pkga": "1.0.1",
        "pkgb": "1.0.2",
        "pkgc": "1.0.3",
        "weird-name-1.2.3-1234.5.6.test7tst.x86_64": "20220214-2.1",
    }
    list_with_weird_installed_ver_list = {
        "pkga": ["1.0.1"],
        "pkgb": ["1.0.2"],
        "pkgc": ["1.0.3"],
        "weird-name-1.2.3-1234.5.6.test7tst.x86_64": ["20220214-2.1"],
    }
    list_pkgs = MagicMock(
        side_effect=[
            list_no_weird_installed_ver_list,
            {},
            list_no_weird_installed,
            list_no_weird_installed_ver_list,
            list_with_weird_installed,
            list_with_weird_installed,
            list_with_weird_installed_ver_list,
        ]
    )

    salt_dict = {
        "pkg.install": yumpkg.install,
        "pkg.list_pkgs": list_pkgs,
        "pkg.normalize_name": yumpkg.normalize_name,
        "pkg_resource.version_clean": pkg_resource.version_clean,
        "pkg_resource.parse_targets": pkg_resource.parse_targets,
    }

    with patch("salt.modules.yumpkg.list_pkgs", list_pkgs), patch(
        "salt.modules.yumpkg.version_cmp", MagicMock(return_value=0)
    ), patch(
        "salt.modules.yumpkg._call_yum", MagicMock(return_value={"retcode": 0})
    ) as call_yum_mock, patch.dict(
        pkg.__salt__, salt_dict
    ), patch.dict(
        pkg_resource.__salt__, salt_dict
    ), patch.dict(
        yumpkg.__salt__, salt_dict
    ):

        expected = {
            "weird-name-1.2.3-1234.5.6.test7tst.x86_64": {
                "old": "",
                "new": "20220214-2.1",
            }
        }
        ret = pkg.installed(
            "test_install",
            pkgs=[{"weird-name-1.2.3-1234.5.6.test7tst.x86_64.noarch": "20220214-2.1"}],
        )
        call_yum_mock.assert_called_once()
        assert (
            call_yum_mock.mock_calls[0].args[0][2]
            == "weird-name-1.2.3-1234.5.6.test7tst.x86_64-20220214-2.1"
        )
        assert ret["result"]
        assert ret["changes"] == expected


def test_removed_with_single_normalize():
    """
    Test pkg.removed with preventing multiple package name normalisation
    """

    list_no_weird_installed = {
        "pkga": "1.0.1",
        "pkgb": "1.0.2",
        "pkgc": "1.0.3",
    }
    list_no_weird_installed_ver_list = {
        "pkga": ["1.0.1"],
        "pkgb": ["1.0.2"],
        "pkgc": ["1.0.3"],
    }
    list_with_weird_installed = {
        "pkga": "1.0.1",
        "pkgb": "1.0.2",
        "pkgc": "1.0.3",
        "weird-name-1.2.3-1234.5.6.test7tst.x86_64": "20220214-2.1",
    }
    list_with_weird_installed_ver_list = {
        "pkga": ["1.0.1"],
        "pkgb": ["1.0.2"],
        "pkgc": ["1.0.3"],
        "weird-name-1.2.3-1234.5.6.test7tst.x86_64": ["20220214-2.1"],
    }
    list_pkgs = MagicMock(
        side_effect=[
            list_with_weird_installed_ver_list,
            list_with_weird_installed,
            list_no_weird_installed,
            list_no_weird_installed_ver_list,
        ]
    )

    salt_dict = {
        "pkg.remove": yumpkg.remove,
        "pkg.list_pkgs": list_pkgs,
        "pkg.normalize_name": yumpkg.normalize_name,
        "pkg_resource.parse_targets": pkg_resource.parse_targets,
        "pkg_resource.version_clean": pkg_resource.version_clean,
    }

    with patch("salt.modules.yumpkg.list_pkgs", list_pkgs), patch(
        "salt.modules.yumpkg.version_cmp", MagicMock(return_value=0)
    ), patch(
        "salt.modules.yumpkg._call_yum", MagicMock(return_value={"retcode": 0})
    ) as call_yum_mock, patch.dict(
        pkg.__salt__, salt_dict
    ), patch.dict(
        pkg_resource.__salt__, salt_dict
    ), patch.dict(
        yumpkg.__salt__, salt_dict
    ):

        expected = {
            "weird-name-1.2.3-1234.5.6.test7tst.x86_64": {
                "old": "20220214-2.1",
                "new": "",
            }
        }
        ret = pkg.removed(
            "test_remove",
            pkgs=[{"weird-name-1.2.3-1234.5.6.test7tst.x86_64.noarch": "20220214-2.1"}],
        )
        call_yum_mock.assert_called_once()
        assert (
            call_yum_mock.mock_calls[0].args[0][2]
            == "weird-name-1.2.3-1234.5.6.test7tst.x86_64-20220214-2.1"
        )
        assert ret["result"]
        assert ret["changes"] == expected
