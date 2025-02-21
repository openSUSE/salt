import time

import pytest

import salt.channel.server as server
import salt.ext.tornado.gen
from tests.support.mock import MagicMock, patch


def test__auth_cmd_stats_passing():
    req_server_channel = server.ReqServerChannel({"master_stats": True}, None)

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
