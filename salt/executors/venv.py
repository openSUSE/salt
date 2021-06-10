"""
Wipe PYTHONHOME environment variable for venvjailed salt-minion
"""
import os


def execute(opts, data, func, args, kwargs):
    """
    Wipe PYTHONHOME environment variable for venvjailed salt-minion
    """
    if os.environ.get("VIRTUAL_ENV", None) == os.environ.get("PYTHONHOME", ""):
        os.environ.pop("PYTHONHOME", None)
    return __executors__["direct_call.execute"](opts, data, func, args, kwargs)
