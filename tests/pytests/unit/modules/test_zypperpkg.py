"""
    :codeauthor: Gareth J. Greenaway <ggreenaway@vmware.com>
"""


import os
import textwrap

import pytest
import salt.modules.pkg_resource as pkg_resource
import salt.modules.zypperpkg as zypper
from salt.exceptions import CommandExecutionError, SaltInvocationError
from tests.support.mock import MagicMock, mock_open, patch


@pytest.fixture
def configure_loader_modules():
    return {
        zypper: {
            "rpm": None,
            "_systemd_scope": MagicMock(return_value=False),
            "osrelease_info": [15, 3],
            "__salt__": {"pkg_resource.parse_targets": pkg_resource.parse_targets},
        },
        pkg_resource: {"__grains__": {"os": "SUSE"}},
    }


@pytest.fixture(autouse=True)
def fresh_zypper_instance():
    zypper.__zypper__ = zypper._Zypper()


def test_list_pkgs_no_context():
    """
    Test packages listing.

    :return:
    """

    def _add_data(data, key, value):
        data.setdefault(key, []).append(value)

    rpm_out = [
        "protobuf-java_|-(none)_|-2.6.1_|-3.1.develHead_|-noarch_|-(none)_|-1499257756",
        "yast2-ftp-server_|-(none)_|-3.1.8_|-8.1_|-x86_64_|-(none)_|-1499257798",
        "jose4j_|-(none)_|-0.4.4_|-2.1.develHead_|-noarch_|-(none)_|-1499257756",
        "apache-commons-cli_|-(none)_|-1.2_|-1.233_|-noarch_|-(none)_|-1498636510",
        "jakarta-commons-discovery_|-(none)_|-0.4_|-129.686_|-noarch_|-(none)_|-1498636511",
        "susemanager-build-keys-web_|-(none)_|-12.0_|-5.1.develHead_|-noarch_|-(none)_|-1498636510",
        "gpg-pubkey_|-(none)_|-39db7c82_|-5847eb1f_|-(none)_|-(none)_|-1519203802",
        "gpg-pubkey_|-(none)_|-8a7c64f9_|-5aaa93ca_|-(none)_|-(none)_|-1529925595",
        "kernel-default_|-(none)_|-4.4.138_|-94.39.1_|-x86_64_|-(none)_|-1529936067",
        "kernel-default_|-(none)_|-4.4.73_|-5.1_|-x86_64_|-(none)_|-1503572639",
        "perseus-dummy_|-(none)_|-1.1_|-1.1_|-i586_|-(none)_|-1529936062",
    ]
    with patch.dict(zypper.__grains__, {"osarch": "x86_64"}), patch.dict(
        zypper.__salt__,
        {"cmd.run": MagicMock(return_value=os.linesep.join(rpm_out))},
    ), patch.dict(zypper.__salt__, {"pkg_resource.add_pkg": _add_data}), patch.dict(
        zypper.__salt__,
        {"pkg_resource.format_pkg_list": pkg_resource.format_pkg_list},
    ), patch.dict(
        zypper.__salt__, {"pkg_resource.stringify": MagicMock()}
    ), patch.object(
        zypper, "_list_pkgs_from_context"
    ) as list_pkgs_context_mock:
        pkgs = zypper.list_pkgs(versions_as_list=True, use_context=False)
        list_pkgs_context_mock.assert_not_called()
        list_pkgs_context_mock.reset_mock()

        pkgs = zypper.list_pkgs(versions_as_list=True, use_context=False)
        list_pkgs_context_mock.assert_not_called()
        list_pkgs_context_mock.reset_mock()


def test_normalize_name():
    """
    Test that package is normalized only when it should be
    """
    with patch.dict(zypper.__grains__, {"osarch": "x86_64"}):
        result = zypper.normalize_name("foo")
        assert result == "foo", result
        result = zypper.normalize_name("foo.x86_64")
        assert result == "foo", result
        result = zypper.normalize_name("foo.noarch")
        assert result == "foo", result

    with patch.dict(zypper.__grains__, {"osarch": "aarch64"}):
        result = zypper.normalize_name("foo")
        assert result == "foo", result
        result = zypper.normalize_name("foo.aarch64")
        assert result == "foo", result
        result = zypper.normalize_name("foo.noarch")
        assert result == "foo", result


def test_get_repo_keys():
    salt_mock = {"lowpkg.list_gpg_keys": MagicMock(return_value=True)}
    with patch.dict(zypper.__salt__, salt_mock):
        assert zypper.get_repo_keys(info=True, root="/mnt")
        salt_mock["lowpkg.list_gpg_keys"].assert_called_once_with(True, "/mnt")


def test_add_repo_key_fail():
    with pytest.raises(SaltInvocationError):
        zypper.add_repo_key()

    with pytest.raises(SaltInvocationError):
        zypper.add_repo_key(path="path", text="text")


def test_add_repo_key_path():
    salt_mock = {
        "cp.cache_file": MagicMock(return_value="path"),
        "lowpkg.import_gpg_key": MagicMock(return_value=True),
    }
    with patch("salt.utils.files.fopen", mock_open(read_data="text")), patch.dict(
        zypper.__salt__, salt_mock
    ):
        assert zypper.add_repo_key(path="path", root="/mnt")
        salt_mock["cp.cache_file"].assert_called_once_with("path", "base")
        salt_mock["lowpkg.import_gpg_key"].assert_called_once_with("text", "/mnt")


def test_add_repo_key_text():
    salt_mock = {"lowpkg.import_gpg_key": MagicMock(return_value=True)}
    with patch.dict(zypper.__salt__, salt_mock):
        assert zypper.add_repo_key(text="text", root="/mnt")
        salt_mock["lowpkg.import_gpg_key"].assert_called_once_with("text", "/mnt")


def test_del_repo_key():
    salt_mock = {"lowpkg.remove_gpg_key": MagicMock(return_value=True)}
    with patch.dict(zypper.__salt__, salt_mock):
        assert zypper.del_repo_key(keyid="keyid", root="/mnt")
        salt_mock["lowpkg.remove_gpg_key"].assert_called_once_with("keyid", "/mnt")


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


@pytest.mark.parametrize(
    "zypper_version,lowpkg_version_cmp,expected_inst_avc,expected_dup_avc",
    [
        ("0.5", [-1, -1], False, False),
        ("1.11.34", [0, -1], False, True),
        ("1.14.8", [0, 0], True, True),
    ],
)
def test_refresh_zypper_flags(
    zypper_version, lowpkg_version_cmp, expected_inst_avc, expected_dup_avc
):
    with patch(
        "salt.modules.zypperpkg.version", MagicMock(return_value=zypper_version)
    ), patch.dict(
        zypper.__salt__,
        {"lowpkg.version_cmp": MagicMock(side_effect=lowpkg_version_cmp)},
    ):
        _zypper = zypper._Zypper()
        _zypper.refresh_zypper_flags()
        assert _zypper.inst_avc == expected_inst_avc
        assert _zypper.dup_avc == expected_dup_avc


@pytest.mark.parametrize(
    "inst_avc,dup_avc,avc,allowvendorchange_param,novendorchange_param,expected",
    [
        # inst_avc = True, dup_avc = True
        (True, True, False, False, False, True),
        (True, True, False, True, False, True),
        (True, True, False, False, True, False),
        (True, True, False, True, True, True),
        # inst_avc = False, dup_avc = True
        (False, True, False, False, False, True),
        (False, True, False, True, False, True),
        (False, True, False, False, True, False),
        (False, True, False, True, True, True),
        # inst_avc = False, dup_avc = False
        (False, False, False, False, False, False),
        (False, False, False, True, False, False),
        (False, False, False, False, True, False),
        (False, False, False, True, True, False),
    ],
)
@patch("salt.modules.zypperpkg._Zypper.refresh_zypper_flags", MagicMock())
def test_allow_vendor_change(
    inst_avc,
    dup_avc,
    avc,
    allowvendorchange_param,
    novendorchange_param,
    expected,
):
    _zypper = zypper._Zypper()
    _zypper.inst_avc = inst_avc
    _zypper.dup_avc = dup_avc
    _zypper.avc = avc
    _zypper.allow_vendor_change(allowvendorchange_param, novendorchange_param)
    assert _zypper.avc == expected


@pytest.mark.parametrize(
    "package,pre_version,post_version,fromrepo_param,name_param,pkgs_param,diff_attr_param",
    [
        ("vim", "1.1", "1.2", [], "", [], "all"),
        ("kernel-default", "1.1", "1.1,1.2", ["dummy", "dummy2"], "", [], None),
        ("vim", "1.1", "1.2", [], "vim", [], None),
    ],
)
@patch.object(zypper, "refresh_db", MagicMock(return_value=True))
def test_upgrade(
    package,
    pre_version,
    post_version,
    fromrepo_param,
    name_param,
    pkgs_param,
    diff_attr_param,
):
    with patch(
        "salt.modules.zypperpkg.__zypper__.noraise.call"
    ) as zypper_mock, patch.object(
        zypper,
        "list_pkgs",
        MagicMock(side_effect=[{package: pre_version}, {package: post_version}]),
    ) as list_pkgs_mock:
        expected_call = ["update", "--auto-agree-with-licenses"]
        for repo in fromrepo_param:
            expected_call.extend(["--repo", repo])

        if pkgs_param:
            expected_call.extend(pkgs_param)
        elif name_param:
            expected_call.append(name_param)

        result = zypper.upgrade(
            name=name_param,
            pkgs=pkgs_param,
            fromrepo=fromrepo_param,
            diff_attr=diff_attr_param,
        )
        zypper_mock.assert_any_call(*expected_call)
        assert result == {package: {"old": pre_version, "new": post_version}}
        list_pkgs_mock.assert_any_call(root=None, attr=diff_attr_param)


@pytest.mark.parametrize(
    "package,pre_version,post_version,fromrepo_param",
    [
        ("vim", "1.1", "1.2", []),
        ("emacs", "1.1", "1.2", ["Dummy", "Dummy2"]),
    ],
)
@patch.object(zypper, "refresh_db", MagicMock(return_value=True))
def test_dist_upgrade(package, pre_version, post_version, fromrepo_param):
    with patch(
        "salt.modules.zypperpkg.__zypper__.noraise.call"
    ) as zypper_mock, patch.object(
        zypper,
        "list_pkgs",
        MagicMock(side_effect=[{package: pre_version}, {package: post_version}]),
    ):
        expected_call = ["dist-upgrade", "--auto-agree-with-licenses"]

        for repo in fromrepo_param:
            expected_call.extend(["--from", repo])

        result = zypper.upgrade(dist_upgrade=True, fromrepo=fromrepo_param)
        zypper_mock.assert_any_call(*expected_call)
        assert result == {package: {"old": pre_version, "new": post_version}}


@pytest.mark.parametrize(
    "package,pre_version,post_version,dup_avc,novendorchange_param,allowvendorchange_param,vendor_change",
    [
        # dup_avc = True, both params = default -> no vendor change
        ("vim", "1.1", "1.2", True, True, False, False),
        # dup_avc = True, allowvendorchange = True -> vendor change
        (
            "emacs",
            "1.1",
            "1.2",
            True,
            True,
            True,
            True,
        ),
        # dup_avc = True, novendorchange = False -> vendor change
        ("joe", "1.1", "1.2", True, False, False, True),
        # dup_avc = True, both params = toggled -> vendor change
        ("kate", "1.1", "1.2", True, False, True, True),
         # dup_avc = False -> no vendor change
        (
            "gedit",
            "1.1",
            "1.2",
            False,
            False,
            True,
            False
        ),
    ],
)
@patch.object(zypper, "refresh_db", MagicMock(return_value=True))
def test_dist_upgrade_vendorchange(
    package,
    pre_version,
    post_version,
    dup_avc,
    novendorchange_param,
    allowvendorchange_param,
    vendor_change
):
    cmd_run_mock = MagicMock(return_value={"retcode": 0, "stdout": None})
    with patch.object(
        zypper,
        "list_pkgs",
        MagicMock(side_effect=[{package: pre_version}, {package: post_version}]),
    ), patch("salt.modules.zypperpkg.__zypper__.refresh_zypper_flags",), patch.dict(
        zypper.__salt__, {"cmd.run_all": cmd_run_mock}
    ):
        expected_cmd = ["zypper", "--non-interactive", "--no-refresh", "dist-upgrade"]
        # --allow-vendor-change is injected right after "dist-upgrade"
        if vendor_change:
            expected_cmd.append("--allow-vendor-change")
        expected_cmd.append("--auto-agree-with-licenses")

        zypper.__zypper__.dup_avc = dup_avc
        zypper.upgrade(
            dist_upgrade=True,
            allowvendorchange=allowvendorchange_param,
            novendorchange=novendorchange_param,
        )
        cmd_run_mock.assert_any_call(
            expected_cmd, output_loglevel="trace", python_shell=False, env={}
        )


@pytest.mark.parametrize(
    "package,pre_version,post_version,fromrepo_param",
    [
        ("vim", "1.1", "1.1", []),
        ("emacs", "1.1", "1.1", ["Dummy", "Dummy2"]),
    ],
)
@patch.object(zypper, "refresh_db", MagicMock(return_value=True))
def test_dist_upgrade_dry_run(package, pre_version, post_version, fromrepo_param):
    with patch(
        "salt.modules.zypperpkg.__zypper__.noraise.call"
    ) as zypper_mock, patch.object(
        zypper,
        "list_pkgs",
        MagicMock(side_effect=[{package: pre_version}, {package: post_version}]),
    ):
        expected_call = ["dist-upgrade", "--auto-agree-with-licenses", "--dry-run"]

        for repo in fromrepo_param:
            expected_call.extend(["--from", repo])

        zypper.upgrade(dist_upgrade=True, dryrun=True, fromrepo=fromrepo_param)
        zypper_mock.assert_any_call(*expected_call)
        # dryrun=True causes two calls, one with a trailing --debug-solver flag
        expected_call.append("--debug-solver")
        zypper_mock.assert_any_call(*expected_call)


@patch.object(zypper, "refresh_db", MagicMock(return_value=True))
def test_dist_upgrade_failure():
    zypper_output = textwrap.dedent(
        """\
        Loading repository data...
        Reading installed packages...
        Computing distribution upgrade...
        Use 'zypper repos' to get the list of defined repositories.
        Repository 'DUMMY' not found by its alias, number, or URI.
        """
    )
    call_spy = MagicMock()
    zypper_mock = MagicMock()
    zypper_mock.stdout = zypper_output
    zypper_mock.stderr = ""
    zypper_mock.exit_code = 3
    zypper_mock.noraise.call = call_spy
    with patch("salt.modules.zypperpkg.__zypper__", zypper_mock), patch.object(
        zypper, "list_pkgs", MagicMock(side_effect=[{"vim": 1.1}, {"vim": 1.1}])
    ):
        expected_call = [
            "dist-upgrade",
            "--auto-agree-with-licenses",
            "--from",
            "Dummy",
        ]

        with pytest.raises(CommandExecutionError) as exc:
            zypper.upgrade(dist_upgrade=True, fromrepo=["Dummy"])
            call_spy.assert_called_with(*expected_call)

            assert exc.exception.info["changes"] == {}
            assert exc.exception.info["result"]["stdout"] == zypper_output
