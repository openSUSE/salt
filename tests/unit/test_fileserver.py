# -*- coding: utf-8 -*-
'''
    :codeauthor: Joao Mesquita <jmesquita@sangoma.com>
'''

# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals

import datetime
import os
import time

import salt.utils.files
from salt import fileserver
from tests.support.helpers import with_tempdir

# Import Salt Testing libs
from tests.support.unit import TestCase

from salt import fileserver


class MapDiffTestCase(TestCase):
    def test_diff_with_diffent_keys(self):
        '''
        Test that different maps are indeed reported different
        '''
        map1 = {'file1': 1234}
        map2 = {'file2': 1234}
        assert fileserver.diff_mtime_map(map1, map2) is True

    def test_diff_with_diffent_values(self):
        '''
        Test that different maps are indeed reported different
        '''
        map1 = {'file1': 12345}
        map2 = {'file1': 1234}
        assert fileserver.diff_mtime_map(map1, map2) is True


class VCSBackendWhitelistCase(TestCase):
    def setup_loader_modules(self):
        return {fileserver: {}}

    @with_tempdir()
    def test_future_file_list_cache_file_ignored(self, cachedir):
        opts = {
            "fileserver_backend": ["roots"],
            "cachedir": cachedir,
            "extension_modules": "",
        }

        back_cachedir = os.path.join(cachedir, "file_lists/roots")
        os.makedirs(os.path.join(back_cachedir))

        # Touch a couple files
        for filename in ("base.p", "foo.txt"):
            with salt.utils.files.fopen(
                os.path.join(back_cachedir, filename), "wb"
            ) as _f:
                if filename == "base.p":
                    _f.write(b"\x80")

        # Set modification time to file list cache file to 1 year in the future
        now = datetime.datetime.utcnow()
        future = now + datetime.timedelta(days=365)
        mod_time = time.mktime(future.timetuple())
        os.utime(os.path.join(back_cachedir, "base.p"), (mod_time, mod_time))

        list_cache = os.path.join(back_cachedir, "base.p")
        w_lock = os.path.join(back_cachedir, ".base.w")
        ret = fileserver.check_file_list_cache(opts, "files", list_cache, w_lock)
        assert (
            ret[1] is True
        ), "Cache file list cache file is not refreshed when future modification time"
