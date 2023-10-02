import pytest

from tests.support.mock import MagicMock, patch


def test_saltcmd_batch_async_call():
    """
    Test calling batch async with salt CLI
    """
    import salt.cli.salt

    local_client = MagicMock()
    local_client.run_job = MagicMock(return_value={"jid": 123456})
    with pytest.raises(SystemExit) as exit_info, patch(
        "sys.argv",
        [
            "salt",
            "--batch=10",
            "--async",
            "*",
            "test.arg",
            "arg1",
            "arg2",
            "kwarg1=val1",
        ],
    ), patch("salt.cli.salt.SaltCMD.process_config_dir", MagicMock), patch(
        "salt.output.display_output", MagicMock()
    ), patch(
        "salt.client.get_local_client", return_value=local_client
    ), patch(
        "salt.utils.stringutils.print_cli", MagicMock()
    ) as print_cli:
        salt_cmd = salt.cli.salt.SaltCMD()
        salt_cmd.config = {
            "async": True,
            "batch": 10,
            "tgt": "*",
            "fun": "test.arg",
            "arg": ["arg1", "arg2", {"__kwarg__": True, "kwarg1": "val1"}],
        }
        salt_cmd._mixin_after_parsed_funcs = []
        salt_cmd.run()

        local_client.run_job.assert_called_once()
        assert local_client.run_job.mock_calls[0].args[0] == "*"
        assert local_client.run_job.mock_calls[0].args[1] == "test.arg"
        assert local_client.run_job.mock_calls[0].kwargs["arg"] == ["arg1", "arg2", {"__kwarg__": True, "kwarg1": "val1"}]
        assert local_client.run_job.mock_calls[0].kwargs["batch"] == 10
        print_cli.assert_called_once_with("Executed command with job ID: 123456")
        assert exit_info.value.code == 0
