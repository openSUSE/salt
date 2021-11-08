# -*- coding: utf-8 -*-
"""
Read in the roster from Uyuni DB
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging

import salt.config

# Import Salt libs
import salt.loader

log = logging.getLogger(__name__)

try:
    from spacewalk.common.rhnConfig import CFG, initCFG
    from spacewalk.server import rhnSQL

    HAS_UYUNI = True
except ImportError:
    HAS_UYUNI = False
except TypeError:
    log.warning("Unable to read Uyuni config file: /etc/rhn/rhn.conf")
    HAS_UYUNI = False


__virtualname__ = "uyuni"


COBBLER_HOST = "localhost"
PROXY_SSH_PUSH_USER = "mgrsshtunnel"
PROXY_SSH_PUSH_KEY = (
    "/var/lib/spacewalk/" + PROXY_SSH_PUSH_USER + "/.ssh/id_susemanager_ssh_push"
)
SALT_SSH_CONNECT_TIMEOUT = 180
SSH_KEY_DIR = "/srv/susemanager/salt/salt_ssh"
SSH_KEY_PATH = SSH_KEY_DIR + "/mgr_ssh_id"
SSH_PUSH_PORT = 22
SSH_PUSH_PORT_HTTPS = 1233
SSH_PUSH_SUDO_USER = None
SSL_PORT = 443


def __virtual__():
    global SSH_PUSH_PORT_HTTPS
    global SALT_SSH_CONNECT_TIMEOUT
    global COBBLER_HOST
    if HAS_UYUNI:
        initCFG("web")
        try:
            SSH_PUSH_PORT_HTTPS = int(CFG.SSH_PUSH_PORT_HTTPS)
        except (AttributeError, ValueError):
            log.debug("Unable to get `ssh_push_port_https`. Fallback to default.")
        try:
            SSH_PUSH_SUDO_USER = CFG.SSH_PUSH_SUDO_USER
        except AttributeError:
            log.debug("Unable to get `ssh_push_sudo_user`. Fallback to default.")
        initCFG("java")
        try:
            SALT_SSH_CONNECT_TIMEOUT = int(CFG.SALT_SSH_CONNECT_TIMEOUT)
        except (AttributeError, ValueError):
            log.debug("Unable to get `salt_ssh_connect_timeout`. Fallback to default.")
        log.debug("ssh_push_port_https: %d" % (SSH_PUSH_PORT_HTTPS))
        log.debug("salt_ssh_connect_timeout: %d" % (SALT_SSH_CONNECT_TIMEOUT))
        log.debug("cobbler.host: %s" % (COBBLER_HOST))
    return (HAS_UYUNI and __virtualname__, "Uyuni is not installed on the system")


def targets(tgt, tgt_type="glob", **kwargs):
    """
    Return the targets from the Uyuni DB
    """

    ret = {}
    rhnSQL.initDB()
    sql_servers = """
        SELECT S.id AS server_id,
               S.name AS server_name,
               S.hostname AS server_hostname,
               SSCM.label AS server_contact_method
        FROM rhnServer AS S
        LEFT JOIN suseServerContactMethod AS SSCM ON
             (SSCM.id=S.contact_method_id)
        WHERE SSCM.label IN ('ssh-push', 'ssh-push-tunnel')
    """
    sql_server_path = """
        SELECT SP.hostname AS proxy_hostname
        FROM rhnServerPath AS SP
        WHERE SP.server_id = :server_id
        ORDER BY SP.position DESC
    """
    h = rhnSQL.prepare(sql_servers)
    sph = rhnSQL.prepare(sql_server_path)
    h.execute()
    while True:
        row = h.fetchone_dict()
        if not row:
            break
        user = SSH_PUSH_SUDO_USER if SSH_PUSH_SUDO_USER else "root"
        server = {
            "host": row["server_hostname"],
            "user": user,
            "port": SSH_PUSH_PORT,
            "timeout": SALT_SSH_CONNECT_TIMEOUT,
        }
        tunnel = row["server_contact_method"] == "ssh-push-tunnel"
        if tunnel:
            server.update({"minion_opts": {"master": row["server_hostname"]}})
        sph.execute(server_id=row["server_id"])
        proxies = sph.fetchall_dict()
        if proxies:
            proxyCommand = "ProxyCommand='"
            i = 0
            for proxy in proxies:
                proxyCommand += (
                    "/usr/bin/ssh -i %s -o StrictHostKeyChecking=no -o User=%s %s %s "
                    % (
                        SSH_KEY_PATH if i == 0 else PROXY_SSH_PUSH_KEY,
                        PROXY_SSH_PUSH_USER,
                        "-W %s:%s" % (row["server_hostname"], SSH_PUSH_PORT)
                        if not tunnel and i == len(proxies) - 1
                        else "",
                        proxy["proxy_hostname"],
                    )
                )
                i += 1
            if tunnel:
                fmt_data = {
                    "pushKey": PROXY_SSH_PUSH_KEY,
                    "user": user,
                    "pushPort": SSH_PUSH_PORT_HTTPS,
                    "proxy": proxies[len(proxies) - 1]["proxy_hostname"],
                    "sslPort": SSL_PORT,
                    "minion": row["server_hostname"],
                    "ownKey": "{}{}".format(
                        "/root" if user == "root" else "/home/{}".format(user),
                        "/.ssh/mgr_own_id",
                    ),
                    "sshPort": SSH_PUSH_PORT,
                }
                proxyCommand += (
                    "/usr/bin/ssh -i {pushKey} -o StrictHostKeyChecking=no "
                    "-o User={user} -R {pushPort}:{proxy}:{sslPort} {minion} "
                    "ssh -i {ownKey} -W {minion}:{sshPort} "
                    "-o StrictHostKeyChecking=no -o User={user} {minion}".format(
                        **fmt_data
                    )
                )
            proxyCommand += "'"
            server.update({"ssh_options": [proxyCommand]})
        elif tunnel:
            server.update(
                {
                    "remote_port_forwards": "%d:%s:%d"
                    % (SSH_PUSH_PORT_HTTPS, COBBLER_HOST, SSL_PORT)
                }
            )
        ret[row["server_name"]] = server
    rhnSQL.closeDB()
    return __utils__["roster_matcher.targets"](ret, tgt, tgt_type, "ipv4")
