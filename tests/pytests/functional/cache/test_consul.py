import logging
import os
import socket
import time

import pytest
from saltfactories.utils import random_string

import salt.cache
import salt.loader
from tests.pytests.functional.cache.helpers import run_common_cache_tests

pytest.importorskip(
    "consul",
    reason="Please install python-consul package to use consul data cache driver",
)
docker = pytest.importorskip("docker", minversion="4.0.0")

log = logging.getLogger(__name__)

INSIDE_CONTAINER = os.getenv("HOSTNAME", "") == "salt-test-container"

pytestmark = [
    pytest.mark.slow_test,
    pytest.mark.skip_if_binaries_missing("dockerd"),
    pytest.mark.skipif(INSIDE_CONTAINER, reason="Cannot run in a container"),
]


def confirm_consul_is_ready(timeout_at, container):
    sleeptime = 0.1
    consul_port = container.get_host_port_binding(8500, protocol="tcp")
    while time.time() <= timeout_at:
        time.sleep(sleeptime)
        try:
            with socket.create_connection(("localhost", consul_port), timeout=1) as cli:
                cli.send(b"GET /v1/kv/fnord HTTP/1.1\n\n")
                cli.recv(2048)
                break
        except ConnectionResetError as e:
            if e.errno == 104:
                sleeptime += sleeptime
    else:
        return False
    return True


@pytest.fixture(scope="module")
def consul_container(salt_factories):

    container = salt_factories.get_container(
        random_string("consul-server-"),
        image_name="ghcr.io/saltstack/salt-ci-containers/consul:latest",
        container_run_kwargs={"ports": {"8500/tcp": None}},
        pull_before_start=True,
        skip_on_pull_failure=True,
        skip_if_docker_client_not_connectable=True,
    )
    container.container_start_check(confirm_consul_is_ready, container)

    with container.started() as factory:
        yield factory


@pytest.fixture
def cache(minion_opts, consul_container):
    opts = minion_opts.copy()
    opts["cache"] = "consul"
    opts["consul.host"] = "127.0.0.1"
    opts["consul.port"] = consul_container.get_host_port_binding(8500, protocol="tcp")
    # NOTE: If you would like to ensure that alternate suffixes are properly
    # tested, simply change this value and re-run the tests.
    opts["consul.timestamp_suffix"] = ".frobnosticate"
    cache = salt.cache.factory(opts)
    return cache


@pytest.mark.slow_test
def test_caching(subtests, cache):
    run_common_cache_tests(subtests, cache)
