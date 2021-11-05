from collections import namedtuple

import pytest
import salt.loader_context
import salt.modules.state as state
from tests.support.mock import patch


PillarPair = namedtuple("PillarPair", ["in_memory", "fresh"])
pillar_combinations = [
    (PillarPair({"foo": "bar"}, {"fred": "baz"}), None),
    (PillarPair({"foo": "bar"}, {"fred": "baz", "_errors": ["Failure"]}), ["Failure"]),
    (PillarPair({"foo": "bar"}, None), None),
    (PillarPair({"foo": "bar", "_errors": ["Failure"]}, None), ["Failure"]),
]


@pytest.mark.parametrize("pillar,expected_errors", pillar_combinations)
def test_get_pillar_errors(pillar: PillarPair, expected_errors):
    """
    test _get_pillar_errors function

    There are three cases to consider:
    1. kwargs['force'] is True -> None, no matter what's in pillar/__pillar__
    2. pillar kwarg is available -> only check pillar, no matter what's in __pillar__
    3. pillar kwarg is not available -> check __pillar__
    """
    ctx = salt.loader_context.LoaderContext()
    named_ctx = ctx.named_context("__pillar__", pillar.in_memory)
    with patch("salt.modules.state.__pillar__", named_ctx, create=True):
        assert (
            state._get_pillar_errors(kwargs={"force": True}, pillar=pillar.fresh)
            is None
        )
        assert (
            state._get_pillar_errors(kwargs={}, pillar=pillar.fresh) == expected_errors
        )
