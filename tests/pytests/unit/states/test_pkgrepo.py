"""
    :codeauthor: Tyler Johnson <tjohnson@saltstack.com>
"""

import pytest

import salt.states.pkgrepo as pkgrepo
import salt.utils.files
from tests.support.mock import MagicMock, patch


@pytest.fixture
def configure_loader_modules():
    return {
        pkgrepo: {
            "__opts__": {"test": True},
            "__grains__": {"os": "", "os_family": ""},
            "__env__": "base",
        }
    }


def test_name_change():
    """
    Test when only the key_url is changed that a change is triggered
    """
    kwargs = {
        "name": "deb http://apt.example.com/{{grains['os'] | lower}} {{grains['oscodename']}} main",
        "disabled": False,
        "key_url": "https://mock/changed_gpg.key",
    }

    new = kwargs.copy()
    new["name"] = (
        "deb [arch=amd64] http://apt.example.com/{{grains['os'] | lower}} {{grains['oscodename']}} main"
    )

    with patch.dict(pkgrepo.__salt__, {"pkg.get_repo": MagicMock(return_value=kwargs)}):
        ret = pkgrepo.managed(**new)
        assert ret["changes"] == {"name": {"old": kwargs["name"], "new": new["name"]}}


def test_new_key_url():
    """
    Test when only the key_url is changed that a change is triggered
    """
    kwargs = {
        "name": "deb https://mock/ sid main",
        "disabled": False,
    }
    key_url = "https://mock/changed_gpg.key"

    with patch.dict(pkgrepo.__salt__, {"pkg.get_repo": MagicMock(return_value=kwargs)}):
        ret = pkgrepo.managed(key_url=key_url, **kwargs)
        assert ret["changes"] == {"key_url": {"old": None, "new": key_url}}


def test_update_key_url():
    """
    Test when only the key_url is changed that a change is triggered
    """
    kwargs = {
        "name": "deb https://mock/ sid main",
        "gpgcheck": 1,
        "disabled": False,
        "key_url": "https://mock/gpg.key",
    }
    changed_kwargs = kwargs.copy()
    changed_kwargs["key_url"] = "https://mock/gpg2.key"

    with patch.dict(pkgrepo.__salt__, {"pkg.get_repo": MagicMock(return_value=kwargs)}):
        ret = pkgrepo.managed(**changed_kwargs)
        assert "key_url" in ret["changes"], "Expected a change to key_url"
        assert ret["changes"] == {
            "key_url": {"old": kwargs["key_url"], "new": changed_kwargs["key_url"]}
        }


def test_managed_insecure_key():
    """
    Test when only the key_url is changed that a change is triggered
    """
    kwargs = {
        "name": "deb http://mock/ sid main",
        "gpgcheck": 1,
        "disabled": False,
        "key_url": "http://mock/gpg.key",
        "allow_insecure_key": False,
    }
    with patch.dict(pkgrepo.__salt__, {"pkg.get_repo": MagicMock(return_value=kwargs)}):
        ret = pkgrepo.managed(**kwargs)
        assert ret["result"] is False
        assert (
            ret["comment"]
            == "Cannot have 'key_url' using http with 'allow_insecure_key' set to True"
        )


def test_managed_clean_file_with_matching_existing_repo_68208(tmp_path):
    """
    Regression test for #68208.

    When pkgrepo.managed is called with ``clean_file: True`` and the desired
    repo line already exists in the file *alongside other stale lines*,
    the state must still empty the file and reconfigure the repo. Prior to
    the fix it would return ``already configured`` and silently skip the
    clean+reconfigure, leaving the stale lines in place.
    """
    backports_file = tmp_path / "backports.list"
    desired_line = "deb http://deb.debian.org/debian bookworm-backports main"
    stale_line = "deb http://deb.debian.org/debian bullseye-backports main"
    backports_file.write_text(stale_line + "\n" + desired_line + "\n")

    kwargs = {
        "name": desired_line,
        "disabled": False,
        "file": str(backports_file),
        "clean_file": True,
    }
    # pkg.get_repo returns the matching definition because the desired
    # line is already present (along with an unrelated stale entry).
    get_repo = MagicMock(return_value=kwargs.copy())
    mod_repo = MagicMock(return_value=None)

    # We want salt.utils.files.fopen to behave normally for the file-read
    # (probing for stale content) but be observable for the "w" truncation
    # call. Use a wrapper that delegates to the real fopen.
    real_fopen = salt.utils.files.fopen
    fopen_calls = []

    def _track_fopen(*args, **kw):
        fopen_calls.append((args, kw))
        return real_fopen(*args, **kw)

    with patch.dict(
        pkgrepo.__salt__,
        {"pkg.get_repo": get_repo, "pkg.mod_repo": mod_repo},
    ), patch.dict(pkgrepo.__opts__, {"test": False}), patch.dict(
        pkgrepo.__grains__,
        {"os": "Debian", "os_family": "Debian", "oscodename": "bookworm"},
    ), patch(
        "salt.modules.aptpkg._expand_repo_def",
        MagicMock(side_effect=lambda os_name, os_codename, repo, **kw: kw),
    ), patch(
        "salt.utils.files.fopen", side_effect=_track_fopen
    ), patch(
        "salt.utils.path.which", MagicMock(return_value=None)
    ):
        ret = pkgrepo.managed(**kwargs)

    # The state must NOT short-circuit with "already configured" when
    # clean_file is requested and there is stale content in the file.
    assert ret["comment"] != (
        "Package repo '{}' already configured".format(kwargs["name"])
    )
    # The file must have been opened for writing (truncation) before
    # pkg.mod_repo is invoked.
    assert ((str(backports_file), "w"), {}) in fopen_calls
    # pkg.mod_repo must be called so the repo line is re-written to the
    # now-empty file.
    assert mod_repo.called


def test_managed_clean_file_with_only_desired_line_no_changes_68208(tmp_path):
    """
    Companion to #68208 regression. When ``clean_file: True`` is set and
    the managed file already contains exactly (and only) the desired repo
    line, the state must still short-circuit to "already configured" so
    repeated runs are idempotent. Without this, the fix for #68208 would
    falsely report a change on every run.
    """
    backports_file = tmp_path / "backports.list"
    desired_line = "deb http://deb.debian.org/debian bookworm-backports main"
    backports_file.write_text(desired_line + "\n")

    kwargs = {
        "name": desired_line,
        "disabled": False,
        "file": str(backports_file),
        "clean_file": True,
    }
    get_repo = MagicMock(return_value=kwargs.copy())
    mod_repo = MagicMock(return_value=None)

    with patch.dict(
        pkgrepo.__salt__,
        {"pkg.get_repo": get_repo, "pkg.mod_repo": mod_repo},
    ), patch.dict(pkgrepo.__opts__, {"test": False}), patch.dict(
        pkgrepo.__grains__,
        {"os": "Debian", "os_family": "Debian", "oscodename": "bookworm"},
    ), patch(
        "salt.modules.aptpkg._expand_repo_def",
        MagicMock(side_effect=lambda os_name, os_codename, repo, **kw: kw),
    ), patch(
        "salt.utils.path.which", MagicMock(return_value=None)
    ):
        ret = pkgrepo.managed(**kwargs)

    assert ret["comment"] == (
        "Package repo '{}' already configured".format(kwargs["name"])
    )
    assert ret["changes"] == {}
    assert not mod_repo.called


def test__normalize_repo_suse():
    repo = {
        "name": "repo name",
        "autorefresh": True,
        "priority": 0,
        "pkg_gpgcheck": True,
    }
    grains = {"os_family": "Suse"}
    with patch.dict(pkgrepo.__grains__, grains):
        assert pkgrepo._normalize_repo(repo) == {
            "humanname": "repo name",
            "refresh": True,
            "priority": 0,
        }


def test__normalize_key_rpm():
    key = {"Description": "key", "Date": "Date", "Other": "Other"}
    for os_family in ("Suse", "RedHat"):
        grains = {"os_family": os_family}
        with patch.dict(pkgrepo.__grains__, grains):
            assert pkgrepo._normalize_key(key) == {"key": "key"}


def test__repos_keys_migrate_drop_migrate_to_empty():
    src_repos = {
        "repo-1": {
            "name": "repo name 1",
            "autorefresh": True,
            "priority": 0,
            "pkg_gpgcheck": True,
        },
        "repo-2": {
            "name": "repo name 2",
            "autorefresh": True,
            "priority": 0,
            "pkg_gpgcheck": False,
        },
    }
    tgt_repos = {}

    src_keys = {
        "key1": {"Description": "key1", "Other": "Other1"},
        "key2": {"Description": "key2", "Other": "Other2"},
    }
    tgt_keys = {}

    grains = {"os_family": "Suse"}
    salt_mock = {
        "pkg.list_repos": MagicMock(side_effect=[src_repos, tgt_repos]),
        "lowpkg.list_gpg_keys": MagicMock(side_effect=[src_keys, tgt_keys]),
    }
    with patch.dict(pkgrepo.__grains__, grains), patch.dict(
        pkgrepo.__salt__, salt_mock
    ):
        assert pkgrepo._repos_keys_migrate_drop("/mnt", False, False) == (
            {
                (
                    "repo-1",
                    (
                        ("humanname", "repo name 1"),
                        ("priority", 0),
                        ("refresh", True),
                    ),
                ),
                (
                    "repo-2",
                    (
                        ("humanname", "repo name 2"),
                        ("priority", 0),
                        ("refresh", True),
                    ),
                ),
            },
            set(),
            set(),
            set(),
        )


def test__repos_keys_migrate_drop_migrate_to_empty_keys():
    src_repos = {
        "repo-1": {
            "name": "repo name 1",
            "autorefresh": True,
            "priority": 0,
            "pkg_gpgcheck": True,
        },
        "repo-2": {
            "name": "repo name 2",
            "autorefresh": True,
            "priority": 0,
            "pkg_gpgcheck": False,
        },
    }
    tgt_repos = {}

    src_keys = {
        "key1": {"Description": "key1", "Other": "Other1"},
        "key2": {"Description": "key2", "Other": "Other2"},
    }
    tgt_keys = {}

    grains = {"os_family": "Suse"}
    salt_mock = {
        "pkg.list_repos": MagicMock(side_effect=[src_repos, tgt_repos]),
        "lowpkg.list_gpg_keys": MagicMock(side_effect=[src_keys, tgt_keys]),
    }
    with patch.dict(pkgrepo.__grains__, grains), patch.dict(
        pkgrepo.__salt__, salt_mock
    ):
        assert pkgrepo._repos_keys_migrate_drop("/mnt", True, False) == (
            {
                (
                    "repo-1",
                    (
                        ("humanname", "repo name 1"),
                        ("priority", 0),
                        ("refresh", True),
                    ),
                ),
                (
                    "repo-2",
                    (
                        ("humanname", "repo name 2"),
                        ("priority", 0),
                        ("refresh", True),
                    ),
                ),
            },
            set(),
            {("key1", (("key", "key1"),)), ("key2", (("key", "key2"),))},
            set(),
        )


def test__repos_keys_migrate_drop_migrate_to_populated_no_drop():
    src_repos = {
        "repo-1": {
            "name": "repo name 1",
            "autorefresh": True,
            "priority": 0,
            "pkg_gpgcheck": True,
        },
        "repo-2": {
            "name": "repo name 2",
            "autorefresh": True,
            "priority": 0,
            "pkg_gpgcheck": False,
        },
    }
    tgt_repos = {
        "repo-1": {
            "name": "repo name 1",
            "autorefresh": True,
            "priority": 0,
            "pkg_gpgcheck": True,
        },
        "repo-3": {
            "name": "repo name 3",
            "autorefresh": True,
            "priority": 0,
            "pkg_gpgcheck": False,
        },
    }

    src_keys = {
        "key1": {"Description": "key1", "Other": "Other1"},
        "key2": {"Description": "key2", "Other": "Other2"},
    }
    tgt_keys = {
        "key1": {"Description": "key1", "Other": "Other1"},
        "key3": {"Description": "key3", "Other": "Other2"},
    }

    grains = {"os_family": "Suse"}
    salt_mock = {
        "pkg.list_repos": MagicMock(side_effect=[src_repos, tgt_repos]),
        "lowpkg.list_gpg_keys": MagicMock(side_effect=[src_keys, tgt_keys]),
    }
    with patch.dict(pkgrepo.__grains__, grains), patch.dict(
        pkgrepo.__salt__, salt_mock
    ):
        assert pkgrepo._repos_keys_migrate_drop("/mnt", True, False) == (
            {
                (
                    "repo-2",
                    (
                        ("humanname", "repo name 2"),
                        ("priority", 0),
                        ("refresh", True),
                    ),
                ),
            },
            set(),
            {("key2", (("key", "key2"),))},
            set(),
        )


def test__repos_keys_migrate_drop_migrate_to_populated_drop():
    src_repos = {
        "repo-1": {
            "name": "repo name 1",
            "autorefresh": True,
            "priority": 0,
            "pkg_gpgcheck": True,
        },
        "repo-2": {
            "name": "repo name 2",
            "autorefresh": True,
            "priority": 0,
            "pkg_gpgcheck": False,
        },
    }
    tgt_repos = {
        "repo-1": {
            "name": "repo name 1",
            "autorefresh": True,
            "priority": 0,
            "pkg_gpgcheck": True,
        },
        "repo-3": {
            "name": "repo name 3",
            "autorefresh": True,
            "priority": 0,
            "pkg_gpgcheck": False,
        },
    }

    src_keys = {
        "key1": {"Description": "key1", "Other": "Other1"},
        "key2": {"Description": "key2", "Other": "Other2"},
    }
    tgt_keys = {
        "key1": {"Description": "key1", "Other": "Other1"},
        "key3": {"Description": "key3", "Other": "Other2"},
    }

    grains = {"os_family": "Suse"}
    salt_mock = {
        "pkg.list_repos": MagicMock(side_effect=[src_repos, tgt_repos]),
        "lowpkg.list_gpg_keys": MagicMock(side_effect=[src_keys, tgt_keys]),
    }
    with patch.dict(pkgrepo.__grains__, grains), patch.dict(
        pkgrepo.__salt__, salt_mock
    ):
        assert pkgrepo._repos_keys_migrate_drop("/mnt", True, True) == (
            {
                (
                    "repo-2",
                    (
                        ("humanname", "repo name 2"),
                        ("priority", 0),
                        ("refresh", True),
                    ),
                ),
            },
            {
                (
                    "repo-3",
                    (
                        ("humanname", "repo name 3"),
                        ("priority", 0),
                        ("refresh", True),
                    ),
                ),
            },
            {("key2", (("key", "key2"),))},
            {("key3", (("key", "key3"),))},
        )


@pytest.mark.skip_on_windows(reason="Not a Windows test")
def test__copy_repository_to_suse():
    grains = {"os_family": "Suse"}
    salt_mock = {"file.copy": MagicMock()}
    with patch.dict(pkgrepo.__grains__, grains), patch.dict(
        pkgrepo.__salt__, salt_mock
    ):
        pkgrepo._copy_repository_to("/mnt")
        salt_mock["file.copy"].assert_called_with(
            src="/etc/zypp/repos.d", dst="/mnt/etc/zypp/repos.d", recurse=True
        )


def test_migrated_non_supported_platform():
    grains = {"os_family": "Debian"}
    with patch.dict(pkgrepo.__grains__, grains):
        assert pkgrepo.migrated("/mnt") == {
            "name": "/mnt",
            "result": False,
            "changes": {},
            "comment": "Migration not supported for this platform",
        }


def test_migrated_missing_keys_api():
    grains = {"os_family": "Suse"}
    with patch.dict(pkgrepo.__grains__, grains):
        assert pkgrepo.migrated("/mnt") == {
            "name": "/mnt",
            "result": False,
            "changes": {},
            "comment": "Keys cannot be migrated for this platform",
        }


def test_migrated_wrong_method():
    grains = {"os_family": "Suse"}
    salt_mock = {
        "lowpkg.import_gpg_key": True,
    }
    with patch.dict(pkgrepo.__grains__, grains), patch.dict(
        pkgrepo.__salt__, salt_mock
    ):
        assert pkgrepo.migrated("/mnt", method_="magic") == {
            "name": "/mnt",
            "result": False,
            "changes": {},
            "comment": "Migration method not supported",
        }


@patch(
    "salt.states.pkgrepo._repos_keys_migrate_drop",
    MagicMock(return_value=(set(), set(), set(), set())),
)
def test_migrated_empty():
    grains = {"os_family": "Suse"}
    salt_mock = {
        "lowpkg.import_gpg_key": True,
    }
    with patch.dict(pkgrepo.__grains__, grains), patch.dict(
        pkgrepo.__salt__, salt_mock
    ):
        assert pkgrepo.migrated("/mnt") == {
            "name": "/mnt",
            "result": True,
            "changes": {},
            "comment": "Repositories are already migrated",
        }


def test_migrated():
    _repos_keys_migrate_drop = MagicMock()
    _repos_keys_migrate_drop.side_effect = [
        (
            {
                (
                    "repo-1",
                    (
                        ("humanname", "repo name 1"),
                        ("priority", 0),
                        ("refresh", True),
                    ),
                ),
            },
            {
                (
                    "repo-2",
                    (
                        ("humanname", "repo name 2"),
                        ("priority", 0),
                        ("refresh", True),
                    ),
                ),
            },
            {("key1", (("key", "key1"),))},
            {("key2", (("key", "key2"),))},
        ),
        (set(), set(), set(), set()),
    ]

    grains = {"os_family": "Suse"}
    opts = {"test": False}
    salt_mock = {
        "pkg.mod_repo": MagicMock(),
        "pkg.del_repo": MagicMock(),
        "lowpkg.import_gpg_key": MagicMock(),
        "lowpkg.remove_gpg_key": MagicMock(),
    }
    with patch.dict(pkgrepo.__grains__, grains), patch.dict(
        pkgrepo.__opts__, opts
    ), patch.dict(pkgrepo.__salt__, salt_mock), patch(
        "salt.states.pkgrepo._repos_keys_migrate_drop", _repos_keys_migrate_drop
    ):
        assert pkgrepo.migrated("/mnt", True, True) == {
            "name": "/mnt",
            "result": True,
            "changes": {
                "repos migrated": ["repo-1"],
                "repos dropped": ["repo-2"],
                "keys migrated": ["key1"],
                "keys dropped": ["key2"],
            },
            "comment": "Repositories synchronized",
        }
        salt_mock["pkg.mod_repo"].assert_called_with(
            "repo-1", humanname="repo name 1", priority=0, refresh=True, root="/mnt"
        )
        salt_mock["pkg.del_repo"].assert_called_with("repo-2", root="/mnt")
        salt_mock["lowpkg.import_gpg_key"].assert_called_with("key1", root="/mnt")
        salt_mock["lowpkg.remove_gpg_key"].assert_called_with("key2", root="/mnt")


def test_migrated_test():
    _repos_keys_migrate_drop = MagicMock()
    _repos_keys_migrate_drop.return_value = (
        {
            (
                "repo-1",
                (("humanname", "repo name 1"), ("priority", 0), ("refresh", True)),
            ),
        },
        {
            (
                "repo-2",
                (("humanname", "repo name 2"), ("priority", 0), ("refresh", True)),
            ),
        },
        {("key1", (("key", "key1"),))},
        {("key2", (("key", "key2"),))},
    )

    grains = {"os_family": "Suse"}
    opts = {"test": True}
    salt_mock = {
        "lowpkg.import_gpg_key": True,
    }
    with patch.dict(pkgrepo.__grains__, grains), patch.dict(
        pkgrepo.__opts__, opts
    ), patch.dict(pkgrepo.__salt__, salt_mock), patch(
        "salt.states.pkgrepo._repos_keys_migrate_drop", _repos_keys_migrate_drop
    ):
        assert pkgrepo.migrated("/mnt", True, True) == {
            "name": "/mnt",
            "result": None,
            "changes": {
                "repos to migrate": ["repo-1"],
                "repos to drop": ["repo-2"],
                "keys to migrate": ["key1"],
                "keys to drop": ["key2"],
            },
            "comment": "There are keys or repositories to migrate or drop",
        }
