import pathlib
import time

import pytest

import salt.master
import salt.utils.platform
from tests.support.mock import MagicMock, patch


@pytest.fixture
def encrypted_requests(tmp_path):
    # To honor the comment on AESFuncs
    return salt.master.AESFuncs(
        opts={
            "cachedir": str(tmp_path / "cache"),
            "sock_dir": str(tmp_path / "sock_drawer"),
            "conf_file": str(tmp_path / "config.conf"),
            "fileserver_backend": "local",
            "master_job_cache": False,
        }
    )


def test_maintenance_duration():
    """
    Validate Maintenance process duration.
    """
    opts = {
        "loop_interval": 10,
        "maintenance_interval": 1,
        "cachedir": "/tmp",
        "sock_dir": "/tmp",
        "maintenance_niceness": 1,
        "key_cache": "sched",
        "conf_file": "",
        "master_job_cache": "",
        "pki_dir": "/tmp",
        "eauth_tokens": "",
    }
    mp = salt.master.Maintenance(opts)
    with patch("salt.utils.verify.check_max_open_files") as check_files, patch.object(
        mp, "handle_key_cache"
    ) as handle_key_cache, patch("salt.daemons") as salt_daemons, patch.object(
        mp, "handle_git_pillar"
    ) as handle_git_pillar:
        mp.run()
    assert salt_daemons.masterapi.clean_old_jobs.called
    assert salt_daemons.masterapi.clean_expired_tokens.called
    assert salt_daemons.masterapi.clean_pub_auth.called
    assert handle_git_pillar.called


def test_fileserver_duration():
    """
    Validate Fileserver process duration.
    """
    with patch("salt.master.FileserverUpdate._do_update") as update:
        start = time.time()
        salt.master.FileserverUpdate.update(1, {}, 1)
        end = time.time()
        # Interval is equal to timeout so the _do_update method will be called
        # one time.
        update.called_once()
        # Timeout is 1 second
        duration = end - start
        if duration > 2 and salt.utils.platform.spawning_platform():
            # Give spawning platforms some slack
            duration = round(duration, 1)
        assert 2 > duration > 1


@pytest.mark.parametrize(
    "expected_return, payload",
    (
        (
            {
                "jid": "20221107162714826470",
                "id": "example-minion",
                "return": {
                    "pkg_|-linux-install-utils_|-curl_|-installed": {
                        "name": "curl",
                        "changes": {},
                        "result": True,
                        "comment": "All specified packages are already installed",
                        "__sls__": "base-linux.base",
                        "__run_num__": 0,
                        "start_time": "08:27:17.594038",
                        "duration": 32.963,
                        "__id__": "linux-install-utils",
                    },
                },
                "retcode": 0,
                "success": True,
                "fun_args": ["base-linux", {"pillar": {"test": "value"}}],
                "fun": "state.sls",
                "out": "highstate",
            },
            {
                "cmd": "_syndic_return",
                "load": [
                    {
                        "id": "aws.us-east-1.salt-syndic",
                        "jid": "20221107162714826470",
                        "fun": "state.sls",
                        "arg": None,
                        "tgt": None,
                        "tgt_type": None,
                        "load": {
                            "arg": [
                                "base-linux",
                                {"pillar": {"test": "value"}, "__kwarg__": True},
                            ],
                            "cmd": "publish",
                            "fun": "state.sls",
                            "jid": "20221107162714826470",
                            "ret": "",
                            "tgt": "example-minion",
                            "user": "sudo_ubuntu",
                            "kwargs": {
                                "show_jid": False,
                                "delimiter": ":",
                                "show_timeout": True,
                            },
                            "tgt_type": "glob",
                        },
                        "return": {
                            "example-minion": {
                                "return": {
                                    "pkg_|-linux-install-utils_|-curl_|-installed": {
                                        "name": "curl",
                                        "changes": {},
                                        "result": True,
                                        "comment": "All specified packages are already installed",
                                        "__sls__": "base-linux.base",
                                        "__run_num__": 0,
                                        "start_time": "08:27:17.594038",
                                        "duration": 32.963,
                                        "__id__": "linux-install-utils",
                                    },
                                },
                                "retcode": 0,
                                "success": True,
                                "fun_args": [
                                    "base-linux",
                                    {"pillar": {"test": "value"}},
                                ],
                            }
                        },
                        "out": "highstate",
                    }
                ],
                "_stamp": "2022-11-07T16:27:17.965404",
            },
        ),
    ),
)
def test_when_syndic_return_processes_load_then_correct_values_should_be_returned(
    expected_return, payload, encrypted_requests
):
    with patch.object(encrypted_requests, "_return", autospec=True) as fake_return:
        encrypted_requests._syndic_return(payload)
        fake_return.assert_called_with(expected_return)


def test_mworker_pass_context():
    """
    Test of passing the __context__ to pillar ext module loader
    """
    req_channel_mock = MagicMock()
    local_client_mock = MagicMock()

    opts = {
        "req_server_niceness": None,
        "mworker_niceness": None,
        "sock_dir": "/tmp",
        "conf_file": "/tmp/fake_conf",
        "transport": "zeromq",
        "fileserver_backend": ["roots"],
        "file_client": "local",
        "pillar_cache": False,
        "state_top": "top.sls",
        "pillar_roots": {},
    }

    data = {
        "id": "MINION_ID",
        "grains": {},
        "saltenv": None,
        "pillarenv": None,
        "pillar_override": {},
        "extra_minion_data": {},
        "ver": "2",
        "cmd": "_pillar",
    }

    test_context = {"testing": 123}

    def mworker_bind_mock():
        mworker.aes_funcs.run_func(data["cmd"], data)

    with patch("salt.client.get_local_client", local_client_mock), patch(
        "salt.master.ClearFuncs", MagicMock()
    ), patch("salt.minion.MasterMinion", MagicMock()), patch(
        "salt.utils.verify.valid_id", return_value=True
    ), patch(
        "salt.loader.matchers", MagicMock()
    ), patch(
        "salt.loader.render", MagicMock()
    ), patch(
        "salt.loader.utils", MagicMock()
    ), patch(
        "salt.loader.fileserver", MagicMock()
    ), patch(
        "salt.loader.minion_mods", MagicMock()
    ), patch(
        "salt.loader._module_dirs", MagicMock()
    ), patch(
        "salt.loader.LazyLoader", MagicMock()
    ) as loadler_pillars_mock:
        mworker = salt.master.MWorker(opts, {}, {}, [req_channel_mock])

        with patch.object(mworker, "_MWorker__bind", mworker_bind_mock), patch.dict(
            mworker.context, test_context
        ):
            mworker.run()
            assert (
                loadler_pillars_mock.call_args_list[0][1].get("pack").get("__context__")
                == test_context
            )

        loadler_pillars_mock.reset_mock()

        opts.update(
            {
                "pillar_cache": True,
                "pillar_cache_backend": "file",
                "pillar_cache_ttl": 1000,
                "cachedir": "/tmp",
            }
        )

        mworker = salt.master.MWorker(opts, {}, {}, [req_channel_mock])

        with patch.object(mworker, "_MWorker__bind", mworker_bind_mock), patch.dict(
            mworker.context, test_context
        ), patch("salt.utils.cache.CacheFactory.factory", MagicMock()):
            mworker.run()
            assert (
                loadler_pillars_mock.call_args_list[0][1].get("pack").get("__context__")
                == test_context
            )


def test_syndic_return_cache_dir_creation(encrypted_requests):
    """master's cachedir for a syndic will be created by AESFuncs._syndic_return method"""
    cachedir = pathlib.Path(encrypted_requests.opts["cachedir"])
    assert not (cachedir / "syndics").exists()
    encrypted_requests._syndic_return(
        {
            "id": "mamajama",
            "jid": "",
            "return": {},
        }
    )
    assert (cachedir / "syndics").exists()
    assert (cachedir / "syndics" / "mamajama").exists()


def test_syndic_return_cache_dir_creation_traversal(encrypted_requests):
    """
    master's  AESFuncs._syndic_return method cachdir creation is not vulnerable to a directory traversal
    """
    cachedir = pathlib.Path(encrypted_requests.opts["cachedir"])
    assert not (cachedir / "syndics").exists()
    encrypted_requests._syndic_return(
        {
            "id": "../mamajama",
            "jid": "",
            "return": {},
        }
    )
    assert not (cachedir / "syndics").exists()
    assert not (cachedir / "mamajama").exists()
