import time

import pytest

import salt.channel.server as server
import salt.ext.tornado.gen
from tests.support.mock import MagicMock, patch


def test__auth_cmd_stats_passing(master_opts):
    master_opts.update(
        {"master_stats": True}
    )
    req_server_channel = server.ReqServerChannel(master_opts, None)

    fake_ret = {"enc": "clear", "load": b"FAKELOAD"}

    def _auth_mock(*_, **__):
        time.sleep(0.03)
        return fake_ret

    future = salt.ext.tornado.gen.Future()
    future.set_result({})

    with patch.object(req_server_channel, "_auth", _auth_mock):
        req_server_channel.payload_handler = MagicMock(return_value=future)
        req_server_channel.handle_message(
            {"enc": "clear", "load": {"cmd": "_auth", "id": "minion"}}
        )
        cur_time = time.time()
        req_server_channel.payload_handler.assert_called_once()
        assert req_server_channel.payload_handler.call_args[0][0]["cmd"] == "_auth"
        auth_call_duration = (
            cur_time - req_server_channel.payload_handler.call_args[0][0]["_start"]
        )
        assert auth_call_duration >= 0.03
        assert auth_call_duration < 0.05


@pytest.fixture
def root_dir(tmp_path):
    (tmp_path / "var").mkdir()
    (tmp_path / "var" / "cache").mkdir()
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc" / "salt").mkdir()
    (tmp_path / "etc" / "salt" / "pki").mkdir()
    (tmp_path / "etc" / "salt" / "pki" / "minions").mkdir()
    yield tmp_path


def test_req_server_validate_token_removes_token(root_dir):
    opts = {
        "master_uri": "tcp://127.0.0.1:4505",
        "cachedir": str(root_dir / "var" / "cache"),
        "pki_dir": str(root_dir / "etc" / "salt" / "pki"),
    }
    reqsrv = server.ReqServerChannel.factory(opts)
    payload = {
        "load": {
            "id": "minion",
            "tok": "asdf",
        }
    }
    assert reqsrv.validate_token(payload) is False
    assert "tok" not in payload["load"]


def test_req_server_validate_token_removes_token_id_traversal(root_dir):
    opts = {
        "master_uri": "tcp://127.0.0.1:4505",
        "cachedir": str(root_dir / "var" / "cache"),
        "pki_dir": str(root_dir / "etc" / "salt" / "pki"),
    }
    reqsrv = server.ReqServerChannel.factory(opts)
    payload = {
        "load": {
            "id": "minion/../../foo",
            "tok": "asdf",
        }
    }
    assert reqsrv.validate_token(payload) is False
    assert "tok" not in payload["load"]
