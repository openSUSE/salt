from salt.runners import state as state_runner
from tests.support.mixins import LoaderModuleMockMixin
from tests.support.mock import Mock, patch
from tests.support.unit import TestCase


class StateRunnerTest(TestCase, LoaderModuleMockMixin):
    def setup_loader_modules(self):
        return {state_runner: {"__opts__": {}, "__jid_event__": Mock()}}

    def test_orchestrate_single_passes_pillar(self):
        """
        test state.orchestrate_single passes given pillar to state.single
        """
        mock_master_minion = Mock()
        mock_state_single = Mock()
        mock_master_minion.functions = {"state.single": mock_state_single}
        mock_master_minion.opts = {"id": "dummy"}
        test_pillar = {"test_entry": "exists"}
        with patch("salt.minion.MasterMinion", Mock(return_value=mock_master_minion)):
            state_runner.orchestrate_single(
                fun="pillar.get", name="test_entry", pillar=test_pillar
            )
            assert mock_state_single.call_args.kwargs["pillar"] == test_pillar

    def test_orchestrate_single_does_not_pass_none_pillar(self):
        """
        test state.orchestrate_single does not pass pillar=None to state.single
        """
        mock_master_minion = Mock()
        mock_state_single = Mock()
        mock_master_minion.functions = {"state.single": mock_state_single}
        mock_master_minion.opts = {"id": "dummy"}
        with patch("salt.minion.MasterMinion", Mock(return_value=mock_master_minion)):
            state_runner.orchestrate_single(
                fun="pillar.get", name="test_entry", pillar=None
            )
            assert "pillar" not in mock_state_single.call_args.kwargs
