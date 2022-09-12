from __future__ import absolute_import, print_function, unicode_literals

# Import python libs
import logging
import requests
import salt.utils.http as http
import salt.utils.json

# This must be present or the Salt loader won't load this module
__proxyenabled__ = ["redfish"]

__virtualname__ = "redfish"

# Variables are scoped to this module so we can have persistent data
# across calls to fns in here.

GRAINS_CACHE = {}
DETAILS = {}
thisproxy = {}

# Want logging!
log = logging.getLogger(__file__)


def __virtual__():
    return __virtualname__


def init(opts):

    """
    This function gets called when the proxy starts up.
    We check opts to see if a fallback user and password are supplied.
       If they are present, and the primary credentials don't work, then
    we try the backup before failing.
    Whichever set of credentials works is placed in the persistent
    DETAILS dictionary and will be used for further communication with the
    chassis.
    """
    DETAILS["host"] = __opts__["proxy"]["host"]
    DETAILS["admin_username"] = __opts__["proxy"]["username"]
    DETAILS["admin_password"] = __opts__["proxy"]["password"]
    verify = __opts__["proxy"]["verify"]
    if "cert" in __opts__["proxy"].keys():
        cert = __opts__["proxy"]["cert"]
    session = requests.Session()
    session.auth = (DETAILS["admin_username"], DETAILS["admin_password"])
    session.verify = False

    if verify == "true":
        logging.info("SSL verification enabled")
        session.verify = True
        if cert is not None:
            logging.info("SSL Cert: " + cert)
            if "," in cert:
                session.cert = [path.strip() for path in cert.split(",")]
            else:
                session.cert = cert
    elif verify == "false":
        session.verify = False
    DETAILS["session"] = session
    # system_services=__salt__['redfish.get_services'](DETAILS['host'],session)
    # if system_services['result']:
    #    DETAILS['services']=system_services['result']
    log.debug(DETAILS)
    return True


def get_details():
    return DETAILS


def admin_username():
    """
    Return the admin_username in the DETAILS dictionary, or root if there
    is none present
    """
    return DETAILS.get("admin_username", "root")


def admin_password():
    """
    Return the admin_password in the DETAILS dictionary, or 'calvin'
    (the Dell default) if there is none present
    """
    if "admin_password" not in DETAILS:
        log.info("proxy.redfish: No admin_password in DETAILS, returning Dell default")
        return "calvin"

    return DETAILS.get("admin_password", "calvin")


def host():
    return DETAILS["host"]


def _grains(host, user, password):
    """
    Get the grains from the proxied device
    """
    r = __salt__["redfish.get_SystemInfo"](
        host=host, admin_username=user, admin_password=password
    )
    if r["result"]:
        GRAINS_CACHE = r["result"]
    else:
        GRAINS_CACHE = {}
    return GRAINS_CACHE


def grains():
    """
    Get the grains from the proxied device
    """
    if not GRAINS_CACHE:
        return _grains(
            DETAILS["host"], DETAILS["admin_username"], DETAILS["admin_password"]
        )

    return GRAINS_CACHE


def grains_refresh():
    """
    Refresh the grains from the proxied device
    """
    GRAINS_CACHE = {}
    return grains()


def find_credentials():
    """
    Cycle through all the possible credentials and return the first one that
    works
    """

    log.debug(
        "proxy redfish.find_credentials found no valid credentials, using Dell default"
    )
    return ("root", "calvin")


def chconfig(cmd, *args, **kwargs):
    """
    This function is called by the :mod:`salt.modules.chassis.cmd <salt.modules.chassis.cmd>`
    shim.  It then calls whatever is passed in ``cmd``
    inside the :mod:`salt.modules.dracr <salt.modules.dracr>`
    module.
    :param cmd: The command to call inside salt.modules.dracr
    :param args: Arguments that need to be passed to that command
    :param kwargs: Keyword arguments that need to be passed to that command
    :return: Passthrough the return from the dracr module.
    """
    # Strip the __pub_ keys...is there a better way to do this?
    for k in list(kwargs):
        if k.startswith("__pub_"):
            kwargs.pop(k)

    # Catch password reset

    if "redfish." + cmd not in __salt__:
        ret = {"retcode": -1, "message": "redfish." + cmd + " is not available"}
    else:
        ret = __salt__["redfish." + cmd](DETAILS["session"], **kwargs)

    return ret


def ping():
    """
    Is the chassis responding?
    :return: Returns False if the chassis didn't respond, True otherwise.
    """
    r = __salt__["redfish.get_system_info"]()
    if r.get("retcode", 0) == 1:
        return False
    else:
        return True
    try:
        return r["dict"].get("ret", False)
    except Exception:  # pylint: disable=broad-except
        return False


def shutdown(opts):
    """
    Shutdown the connection to the proxied device.
    For this proxy shutdown is a no-op.
    """
    log.debug("redfish proxy shutdown() called...")


def http_get(uri):
    """
    Internal function for HTTP GET method


    Return: dictionary with get result

    """

    # Make request
    details = get_details()
    ret = http.query(
        "https://" + details["host"] + uri,
        verify_ssl=False,
        username=details["admin_username"],
        password=details["admin_password"],
        backend="requests",
    )
    if ret.get("error"):
        return ret
    else:
        if "body" in ret and ret["body"] != "":
            return salt.utils.json.loads(ret.get("body"))
        else:
            return ret


def http_post(uri, headers, payload=None, files=None):
    """
    Internal function for HTTP POST method

    Return: dictionary with get result

    """
    result = {}
    details = get_details()
    if files:
        ret = http.query(
            "https://" + details["host"] + uri,
            method="POST",
            header_dict=headers,
            data_file=files,
            verify_ssl=False,
            username=details["admin_username"],
            password=details["admin_password"],
            backend="requests",
        )
    else:
        ret = http.query(
            "https://" + details["host"] + uri,
            method="POST",
            header_dict=headers,
            data=salt.utils.json.dumps(payload),
            verify_ssl=False,
            headers=True,
            username=details["admin_username"],
            password=details["admin_password"],
            backend="requests",
        )

    if ret.get("error"):
        return ret
    else:
        if "headers" in ret:
            logging.debug(ret.get("headers"))
            result["headers"] = ret.get("headers")

        if "body" in ret and ret["body"] != "":
            logging.debug(ret.get("body"))
            result["body"] = salt.utils.json.loads(ret.get("body"))
        return result


def http_patch(uri, headers, payload):
    """Internal function for HTTP PATCH method

    Return: dictionary with get result

    """

    details = get_details()
    ret = http.query(
        "https://" + details["host"] + uri,
        method="PATCH",
        header_dict=headers,
        data=salt.utils.json.dumps(payload),
        verify_ssl=False,
        username=details["admin_username"],
        password=details["admin_password"],
        backend="requests",
    )
    if ret.get("error"):
        return ret
    else:
        if "body" in ret:
            return salt.utils.json.loads(ret.get("body"))
        else:
            return ret


def http_delete(uri, headers):
    """
    internal function for HTTP PATCH method

    Return: dictionary with get result

    """

    details = get_details()
    ret = http.query(
        "https://" + details["host"] + uri,
        method="DELETE",
        header_dict=headers,
        verify_ssl=False,
        username=details["admin_username"],
        password=details["admin_password"],
        backend="requests",
    )
    if ret.get("error"):
        return ret
    else:
        if "body" in ret:
            return salt.utils.json.loads(ret.get("body"))
        else:
            return ret
