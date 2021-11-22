#!/usr/bin/python3

import textwrap

import pytest

pytestmark = [
    pytest.mark.slow_test,
]

# TODO: remove in favor of
# from saltfactories.utils import StateResult
import attr
@attr.s
class StateResult:
    """
    This class wraps a single salt state return into a more pythonic object in order to simplify assertions

    :param dict raw:
        A single salt state return result

    .. code-block:: python

        def test_user_absent(loaders):
            ret = loaders.states.user.absent(name=random_string("account-", uppercase=False))
            assert ret.result is True
    """

    raw = attr.ib()
    state_id = attr.ib(init=False)
    full_return = attr.ib(init=False)
    filtered = attr.ib(init=False)

    @state_id.default
    def _state_id(self):
        if not isinstance(self.raw, dict):
            raise ValueError("The state result errored: {}".format(self.raw))
        return next(iter(self.raw.keys()))

    @full_return.default
    def _full_return(self):
        return self.raw[self.state_id]

    @filtered.default
    def _filtered_default(self):
        _filtered = {}
        for key, value in self.full_return.items():
            if key.startswith("_") or key in ("duration", "start_time"):
                continue
            _filtered[key] = value
        return _filtered

    @property
    def run_num(self):
        """
        The ``__run_num__`` key on the full state return dictionary
        """
        return self.full_return["__run_num__"] or 0

    @property
    def name(self):
        """
        The ``name`` key on the full state return dictionary
        """
        return self.full_return["name"]

    @property
    def result(self):
        """
        The ``result`` key on the full state return dictionary
        """
        return self.full_return["result"]

    @property
    def changes(self):
        """
        The ``changes`` key on the full state return dictionary
        """
        return self.full_return["changes"]

    @property
    def comment(self):
        """
        The ``comment`` key on the full state return dictionary
        """
        return self.full_return["comment"]

    @property
    def warnings(self):
        """
        The ``warnings`` key on the full state return dictionary
        """
        return self.full_return.get("warnings") or []

    def __contains__(self, key):
        """
        Checks for the existence of ``key`` in the full state return dictionary
        """
        return key in self.full_return

    def __eq__(self, _):
        raise TypeError(
            "Please assert comparisons with {}.filtered instead".format(self.__class__.__name__)
        )

    def __bool__(self):
        raise TypeError(
            "Please assert comparisons with {}.filtered instead".format(self.__class__.__name__)
        )

@pytest.fixture(scope="module")
def reset_pillar(salt_call_cli):
    try:
        # Run tests
        yield
    finally:
        # Refresh pillar once all tests are done.
        ret = salt_call_cli.run("saltutil.refresh_pillar", wait=True)
        assert ret.exitcode == 0
        assert ret.json is True


@pytest.fixture
def testfile_path(tmp_path, base_env_state_tree_root_dir):
    testfile = tmp_path / "testfile"
    sls_contents = textwrap.dedent(
        """
        {}:
          file:
            - managed
            - source: salt://testfile
            - makedirs: true
        """.format(testfile)
    )
    with pytest.helpers.temp_file(
        "sls-id-test.sls", sls_contents, base_env_state_tree_root_dir
    ):
        yield testfile


@pytest.mark.usefixtures("testfile_path", "reset_pillar")
def test_state_apply_aborts_on_pillar_error(
    salt_cli,
    salt_minion,
    base_env_pillar_tree_root_dir,
):
    """
    Test state.apply with error in pillar.
    """
    pillar_top_file = textwrap.dedent(
        """
        base:
          '{}':
            - basic
        """
    ).format(salt_minion.id)
    basic_pillar_file = textwrap.dedent(
        """
        syntax_error
        """
    )

    with pytest.helpers.temp_file(
        "top.sls", pillar_top_file, base_env_pillar_tree_root_dir
    ), pytest.helpers.temp_file(
        "basic.sls", basic_pillar_file, base_env_pillar_tree_root_dir
    ):
        expected_comment = [
            "Pillar failed to render with the following messages:",
            "SLS 'basic' does not render to a dictionary",
        ]
        shell_result = salt_cli.run(
            "state.apply", "sls-id-test", minion_tgt=salt_minion.id
        )
        assert shell_result.exitcode == 1
        assert shell_result.json == expected_comment


@pytest.mark.usefixtures("testfile_path", "reset_pillar")
def test_state_apply_continues_after_pillar_error_is_fixed(
    salt_cli,
    salt_minion,
    base_env_pillar_tree_root_dir,
):
    """
    Test state.apply with error in pillar.
    """
    pillar_top_file = textwrap.dedent(
        """
        base:
          '{}':
            - basic
        """.format(salt_minion.id)
    )
    basic_pillar_file_error = textwrap.dedent(
        """
        syntax_error
        """
    )
    basic_pillar_file = textwrap.dedent(
        """
        syntax_error: Fixed!
        """
    )

    # save pillar render error in minion's in-memory pillar
    with pytest.helpers.temp_file(
        "top.sls", pillar_top_file, base_env_pillar_tree_root_dir
    ), pytest.helpers.temp_file(
        "basic.sls", basic_pillar_file_error, base_env_pillar_tree_root_dir
    ):
        shell_result = salt_cli.run(
            "saltutil.refresh_pillar", minion_tgt=salt_minion.id
        )
        assert shell_result.exitcode == 0

    # run state.apply with fixed pillar render error
    with pytest.helpers.temp_file(
        "top.sls", pillar_top_file, base_env_pillar_tree_root_dir
    ), pytest.helpers.temp_file(
        "basic.sls", basic_pillar_file, base_env_pillar_tree_root_dir
    ):
        shell_result = salt_cli.run(
            "state.apply", "sls-id-test", minion_tgt=salt_minion.id
        )
        assert shell_result.exitcode == 0
        state_result = StateResult(shell_result.json)
        assert state_result.result is True
        assert state_result.changes == {"diff": "New file", "mode": "0644"}
