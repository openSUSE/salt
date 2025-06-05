"""
:codeauthor: Bo Maryniuk <bo@suse.de>
"""

import importlib.util
import os
import sys

import pytest

from tests.support.mock import MagicMock, patch
from tests.support.unit import TestCase

try:
    from zypp_plugin import BogusIO

    HAS_ZYPP_PLUGIN = True
except ImportError:
    HAS_ZYPP_PLUGIN = False

BUILTINS_OPEN = "builtins.open"

ZYPPNOTIFY_FILE = os.path.sep.join(
    os.path.dirname(__file__).split(os.path.sep)[:-2]
    + ["scripts", "suse", "zypper", "plugins", "commit", "zyppnotify"]
)


def import_zyppnotify():
    spec = importlib.util.spec_from_file_location("zyppnotify", ZYPPNOTIFY_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(not HAS_ZYPP_PLUGIN, reason="zypp_plugin is missing.")
class ZyppPluginsTestCase(TestCase):
    """
    Test shipped libzypp plugins.
    """

    @pytest.mark.skipif(
        not os.path.exists(ZYPPNOTIFY_FILE),
        reason="Required file '{}' does not exist.".format(ZYPPNOTIFY_FILE),
    )
    def test_drift_detector(self):
        """
        Test drift detector for a correct cookie file.
        Returns:

        """
        zyppnotify = import_zyppnotify()
        drift = zyppnotify.DriftDetector()
        drift._get_mtime = MagicMock(return_value=123)
        drift._get_checksum = MagicMock(return_value="deadbeef")
        bogus_io = BogusIO()
        with patch(BUILTINS_OPEN, bogus_io):
            drift.PLUGINEND(None, None)
        self.assertEqual(str(bogus_io), "deadbeef 123\n")
        self.assertEqual(bogus_io.mode, "w")
        self.assertEqual(bogus_io.path, "/var/cache/salt/minion/rpmdb.cookie")
