# -*- coding: utf-8 -*-
'''
    :codeauthor: :email: `Bo Maryniuk <bo@suse.de>`
'''

# Import Python libs
from __future__ import absolute_import

# Import Salt Testing libs
from salttesting import TestCase
from salttesting.helpers import ensure_in_syspath
from salttesting.mock import patch
import errno

ensure_in_syspath('../')

from salt.fileclient import Client


class Makedir(object):
    def __init__(self, exists=False, errno=None):
        self._exists = exists
        self._errno = errno

    def __call__(self, path, mode=0o0777):
        if self._errno or self._exists:
            raise OSError(self._errno or errno.EEXIST,
                          'Errno {0}'.format(self._errno))


class FileclientTestCase(TestCase):
    '''
    Fileclient test
    '''
    opts = {
        'extension_modules': '',
        'cachedir': '/__test__',
    }

    def test_cache_skips_makedirs_on_race_condition(self):
        '''
        If cache contains already a directory, do not raise an exception.
        '''
        with patch('os.path.isfile', lambda prm: False):
            for exists in range(2):
                with patch('os.makedirs', Makedir(exists=bool(exists))):
                    with Client(self.opts)._cache_loc('testfile') as c_ref_itr:
                        assert c_ref_itr == '/__test__/files/base/testfile'

    def test_cache_raises_exception_on_non_eexist_ioerror(self):
        '''
        If makedirs raises other than EEXIST errno, an exception should be raised.
        '''
        with patch('os.path.isfile', lambda prm: False):
            with patch('os.makedirs', Makedir(errno=errno.EREMOTEIO)):
                with self.assertRaises(OSError):
                    with Client(self.opts)._cache_loc('testfile') as c_ref_itr:
                        assert c_ref_itr == '/__test__/files/base/testfile'
