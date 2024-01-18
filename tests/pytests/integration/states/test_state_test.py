def test_failing_sls(salt_master, salt_minion, salt_cli, caplog):
    """
    Test when running state.sls and the state fails.
    When the master stores the job and attempts to send
    an event a KeyError was previously being logged.
    This test ensures we do not log an error when
    attempting to send an event about a failing state.
    """
    statesls = """
    test_state:
      test.fail_without_changes:
        - name: "bla"
    """
    with salt_master.state_tree.base.temp_file("test_failure.sls", statesls):
        ret = salt_cli.run("state.sls", "test_failure", minion_tgt=salt_minion.id)
        for message in caplog.messages:
            assert "Event iteration failed with" not in message


def test_failing_sls_compound(salt_master, salt_minion, salt_cli, caplog):
    """
    Test when running state.sls in a compound command and the state fails.
    When the master stores the job and attempts to send
    an event a KeyError was previously being logged.
    This test ensures we do not log an error when
    attempting to send an event about a failing state.
    """
    statesls = """
    test_state:
      test.fail_without_changes:
        - name: "bla"
    """
    with salt_master.state_tree.base.temp_file("test_failure.sls", statesls):
        ret = salt_cli.run(
            "state.sls,cmd.run", "test_failure,ls", minion_tgt=salt_minion.id
        )
        for message in caplog.messages:
            assert "Event iteration failed with" not in message
