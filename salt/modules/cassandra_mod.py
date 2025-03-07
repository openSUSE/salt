"""

.. warning::

    The `cassandra` module is deprecated in favor of the `cassandra_cql`
    module.

Cassandra NoSQL Database Module

:depends:   - pycassa Cassandra Python adapter
:configuration:
    The location of the 'nodetool' command, host, and thrift port needs to be
    specified via pillar::

        cassandra.nodetool: /usr/local/bin/nodetool
        cassandra.host: localhost
        cassandra.thrift_port: 9160
"""

import logging

import salt.utils.path
from salt.utils.versions import warn_until_date

log = logging.getLogger(__name__)


HAS_PYCASSA = False
try:
    from pycassa.system_manager import SystemManager

    HAS_PYCASSA = True
except ImportError:
    pass


def __virtual__():
    """
    Only load if pycassa is available and the system is configured
    """
    if not HAS_PYCASSA:
        return (
            False,
            "The cassandra execution module cannot be loaded: pycassa not installed.",
        )

    warn_until_date(
        "20260101",
        "The cassandra returner is broken and deprecated, and will be removed"
        " after {date}. Use the cassandra_cql returner instead",
    )

    if HAS_PYCASSA and salt.utils.path.which("nodetool"):
        return "cassandra"
    return (
        False,
        "The cassandra execution module cannot be loaded: nodetool not found.",
    )


def _nodetool(cmd):
    """
    Internal cassandra nodetool wrapper. Some functions are not
    available via pycassa so we must rely on nodetool.
    """
    nodetool = __salt__["config.option"]("cassandra.nodetool")
    host = __salt__["config.option"]("cassandra.host")
    return __salt__["cmd.run_stdout"]("{} -h {} {}".format(nodetool, host, cmd))


def _sys_mgr():
    """
    Return a pycassa system manager connection object
    """
    thrift_port = str(__salt__["config.option"]("cassandra.THRIFT_PORT"))
    host = __salt__["config.option"]("cassandra.host")
    return SystemManager("{}:{}".format(host, thrift_port))


def compactionstats():
    """
    Return compactionstats info

    CLI Example:

    .. code-block:: bash

        salt '*' cassandra.compactionstats
    """
    return _nodetool("compactionstats")


def version():
    """
    Return the cassandra version

    CLI Example:

    .. code-block:: bash

        salt '*' cassandra.version
    """
    return _nodetool("version")


def netstats():
    """
    Return netstats info

    CLI Example:

    .. code-block:: bash

        salt '*' cassandra.netstats
    """
    return _nodetool("netstats")


def tpstats():
    """
    Return tpstats info

    CLI Example:

    .. code-block:: bash

        salt '*' cassandra.tpstats
    """
    return _nodetool("tpstats")


def info():
    """
    Return cassandra node info

    CLI Example:

    .. code-block:: bash

        salt '*' cassandra.info
    """
    return _nodetool("info")


def ring():
    """
    Return cassandra ring info

    CLI Example:

    .. code-block:: bash

        salt '*' cassandra.ring
    """
    return _nodetool("ring")


def keyspaces():
    """
    Return existing keyspaces

    CLI Example:

    .. code-block:: bash

        salt '*' cassandra.keyspaces
    """
    sys = _sys_mgr()
    return sys.list_keyspaces()


def column_families(keyspace=None):
    """
    Return existing column families for all keyspaces
    or just the provided one.

    CLI Example:

    .. code-block:: bash

        salt '*' cassandra.column_families
        salt '*' cassandra.column_families <keyspace>
    """
    sys = _sys_mgr()
    ksps = sys.list_keyspaces()

    if keyspace:
        if keyspace in ksps:
            return list(sys.get_keyspace_column_families(keyspace).keys())
        else:
            return None
    else:
        ret = {}
        for kspace in ksps:
            ret[kspace] = list(sys.get_keyspace_column_families(kspace).keys())

        return ret


def column_family_definition(keyspace, column_family):
    """
    Return a dictionary of column family definitions for the given
    keyspace/column_family

    CLI Example:

    .. code-block:: bash

        salt '*' cassandra.column_family_definition <keyspace> <column_family>

    """
    sys = _sys_mgr()

    try:
        return vars(sys.get_keyspace_column_families(keyspace)[column_family])
    except Exception:  # pylint: disable=broad-except
        log.debug("Invalid Keyspace/CF combination")
        return None
