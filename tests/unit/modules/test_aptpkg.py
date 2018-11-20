# -*- coding: utf-8 -*-
'''
    :synopsis: Unit Tests for Advanced Packaging Tool module 'module.aptpkg'
    :platform: Linux
    :maturity: develop
    versionadded:: 2017.7.0
'''

# Import Python Libs
from __future__ import absolute_import, print_function, unicode_literals
import copy

# Import Salt Testing Libs
from tests.support.mixins import LoaderModuleMockMixin
from tests.support.unit import TestCase, skipIf
from tests.support.mock import Mock, MagicMock, patch, NO_MOCK, NO_MOCK_REASON

# Import Salt Libs
from salt.ext import six
from salt.exceptions import CommandExecutionError, SaltInvocationError
import salt.modules.aptpkg as aptpkg
import pytest
import textwrap


APT_KEY_LIST = r'''
pub:-:1024:17:46181433FBB75451:1104433784:::-:::scSC:
fpr:::::::::C5986B4F1257FFA86632CBA746181433FBB75451:
uid:-::::1104433784::B4D41942D4B35FF44182C7F9D00C99AF27B93AD0::Ubuntu CD Image Automatic Signing Key <cdimage@ubuntu.com>:
'''

REPO_KEYS = {
    '46181433FBB75451': {
        'algorithm': 17,
        'bits': 1024,
        'capability': 'scSC',
        'date_creation': 1104433784,
        'date_expiration': None,
        'fingerprint': 'C5986B4F1257FFA86632CBA746181433FBB75451',
        'keyid': '46181433FBB75451',
        'uid': 'Ubuntu CD Image Automatic Signing Key <cdimage@ubuntu.com>',
        'uid_hash': 'B4D41942D4B35FF44182C7F9D00C99AF27B93AD0',
        'validity': '-'
    }
}

PACKAGES = {
    'wget': '1.15-1ubuntu1.14.04.2'
}

LOWPKG_FILES = {
    'errors': {},
    'packages': {
        'wget': [
            '/.',
            '/etc',
            '/etc/wgetrc',
            '/usr',
            '/usr/bin',
            '/usr/bin/wget',
            '/usr/share',
            '/usr/share/info',
            '/usr/share/info/wget.info.gz',
            '/usr/share/doc',
            '/usr/share/doc/wget',
            '/usr/share/doc/wget/MAILING-LIST',
            '/usr/share/doc/wget/NEWS.gz',
            '/usr/share/doc/wget/AUTHORS',
            '/usr/share/doc/wget/copyright',
            '/usr/share/doc/wget/changelog.Debian.gz',
            '/usr/share/doc/wget/README',
            '/usr/share/man',
            '/usr/share/man/man1',
            '/usr/share/man/man1/wget.1.gz',
        ]
    }
}

LOWPKG_INFO = {
    'wget': {
        'architecture': 'amd64',
        'description': 'retrieves files from the web',
        'homepage': 'http://www.gnu.org/software/wget/',
        'install_date': '2016-08-30T22:20:15Z',
        'maintainer': 'Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>',
        'name': 'wget',
        'section': 'web',
        'source': 'wget',
        'version': '1.15-1ubuntu1.14.04.2'
    }
}

APT_Q_UPDATE = '''
Get:1 http://security.ubuntu.com trusty-security InRelease [65 kB]
Get:2 http://security.ubuntu.com trusty-security/main Sources [120 kB]
Get:3 http://security.ubuntu.com trusty-security/main amd64 Packages [548 kB]
Get:4 http://security.ubuntu.com trusty-security/main i386 Packages [507 kB]
Hit http://security.ubuntu.com trusty-security/main Translation-en
Fetched 1240 kB in 10s (124 kB/s)
Reading package lists...
'''

APT_Q_UPDATE_ERROR = '''
Err http://security.ubuntu.com trusty InRelease

Err http://security.ubuntu.com trusty Release.gpg
Unable to connect to security.ubuntu.com:http:
Reading package lists...
W: Failed to fetch http://security.ubuntu.com/ubuntu/dists/trusty/InRelease

W: Failed to fetch http://security.ubuntu.com/ubuntu/dists/trusty/Release.gpg  Unable to connect to security.ubuntu.com:http:

W: Some index files failed to download. They have been ignored, or old ones used instead.
'''

AUTOREMOVE = '''
Reading package lists... Done
Building dependency tree
Reading state information... Done
0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.
'''

UPGRADE = '''
Reading package lists...
Building dependency tree...
Reading state information...
0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.
'''

UNINSTALL = {
    'tmux': {
        'new': six.text_type(),
        'old': '1.8-5'
    }
}


@skipIf(NO_MOCK, NO_MOCK_REASON)
class AptPkgTestCase(TestCase, LoaderModuleMockMixin):
    '''
    Test cases for salt.modules.aptpkg
    '''

    def setup_loader_modules(self):
        return {aptpkg: {}}

    @patch('salt.modules.aptpkg.__salt__',
           {'pkg_resource.version': MagicMock(return_value=LOWPKG_INFO['wget']['version'])})
    def test_version(self):
        '''
        Test - Returns a string representing the package version or an empty string if
        not installed.
        '''
        assert aptpkg.version(*['wget']) == aptpkg.__salt__['pkg_resource.version']()

    @patch('salt.modules.aptpkg.latest_version', MagicMock(return_value=''))
    def test_upgrade_available(self):
        '''
        Test - Check whether or not an upgrade is available for a given package.
        '''
        assert not aptpkg.upgrade_available('wget')

    @patch('salt.modules.aptpkg.get_repo_keys', MagicMock(return_value=REPO_KEYS))
    @patch('salt.modules.aptpkg.__salt__', {'cmd.run_all': MagicMock(return_value={'retcode': 0, 'stdout': 'OK'})})
    def test_add_repo_key(self):
        '''
        Test - Add a repo key.
        '''
        assert aptpkg.add_repo_key(keyserver='keyserver.ubuntu.com', keyid='FBB75451')

    @patch('salt.modules.aptpkg.get_repo_keys', MagicMock(return_value=REPO_KEYS))
    @patch('salt.modules.aptpkg.__salt__', {'cmd.run_all': MagicMock(return_value={'retcode': 0, 'stdout': 'OK'})})
    def test_add_repo_key_failed(self):
        '''
        Test - Add a repo key using incomplete input data.
        '''
        with pytest.raises(SaltInvocationError) as ex:
            aptpkg.add_repo_key(keyserver='keyserver.ubuntu.com')
        assert ' No keyid or keyid too short for keyserver: keyserver.ubuntu.com' in str(ex)

    def test_get_repo_keys(self):
        '''
        Test - List known repo key details.
        '''
        mock = MagicMock(return_value={
            'retcode': 0,
            'stdout': APT_KEY_LIST
        })
        with patch.dict(aptpkg.__salt__, {'cmd.run_all': mock}):
            self.assertEqual(aptpkg.get_repo_keys(), REPO_KEYS)

    @patch('salt.modules.aptpkg.__salt__', {'lowpkg.file_dict': MagicMock(return_value=LOWPKG_FILES)})
    def test_file_dict(self):
        '''
        Test - List the files that belong to a package, grouped by package.
        '''
        assert aptpkg.file_dict('wget') == LOWPKG_FILES

    @patch('salt.modules.aptpkg.__salt__', {
        'lowpkg.file_list': MagicMock(return_value={'errors': LOWPKG_FILES['errors'],
                                                    'files': LOWPKG_FILES['packages']['wget']})})
    def test_file_list(self):
        '''
        Test 'file_list' function, which is just an alias to the lowpkg 'file_list'

        '''
        assert aptpkg.file_list('wget') == aptpkg.__salt__['lowpkg.file_list']()

    @patch('salt.modules.aptpkg.__salt__', {'cmd.run_stdout': MagicMock(return_value='wget\t\t\t\t\t\tinstall')})
    def test_get_selections(self):
        '''
        Test - View package state from the dpkg database.
        '''
        assert aptpkg.get_selections('wget') == {'install': ['wget']}

    @patch('salt.modules.aptpkg.__salt__', {'lowpkg.info': MagicMock(return_value=LOWPKG_INFO)})
    def test_info_installed(self):
        '''
        Test - Return the information of the named package(s) installed on the system.
        '''
        names = {
            'group': 'section',
            'packager': 'maintainer',
            'url': 'homepage'
        }

        installed = copy.deepcopy(LOWPKG_INFO)
        for name in names:
            if installed['wget'].get(names[name], False):
                installed['wget'][name] = installed['wget'].pop(names[name])

        assert aptpkg.info_installed('wget') == installed

    @patch('salt.modules.aptpkg.__salt__', {'lowpkg.info': MagicMock(return_value=LOWPKG_INFO)})
    def test_info_installed_attr(self):
        '''
        Test info_installed 'attr'.
        This doesn't test 'attr' behaviour per se, since the underlying function is in dpkg.
        The test should simply not raise exceptions for invalid parameter.

        :return:
        '''
        ret = aptpkg.info_installed('emacs', attr='foo,bar')
        assert isinstance(ret, dict)
        assert 'wget' in ret
        assert isinstance(ret['wget'], dict)

        wget_pkg = ret['wget']
        expected_pkg = {'url': 'http://www.gnu.org/software/wget/',
                        'packager': 'Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>', 'name': 'wget',
                        'install_date': '2016-08-30T22:20:15Z', 'description': 'retrieves files from the web',
                        'version': '1.15-1ubuntu1.14.04.2', 'architecture': 'amd64', 'group': 'web', 'source': 'wget'}
        for k in wget_pkg:
            assert k in expected_pkg
            assert wget_pkg[k] == expected_pkg[k]

    @patch('salt.modules.aptpkg.__salt__', {'lowpkg.info': MagicMock(return_value=LOWPKG_INFO)})
    def test_info_installed_all_versions(self):
        '''
        Test info_installed 'all_versions'.
        Since Debian won't return same name packages with the different names,
        this should just return different structure, backward compatible with
        the RPM equivalents.

        :return:
        '''
        print()
        ret = aptpkg.info_installed('emacs', all_versions=True)
        assert isinstance(ret, dict)
        assert 'wget' in ret
        assert isinstance(ret['wget'], list)

        pkgs = ret['wget']

        assert len(pkgs) == 1
        assert isinstance(pkgs[0], dict)

        wget_pkg = pkgs[0]
        expected_pkg = {'url': 'http://www.gnu.org/software/wget/',
                        'packager': 'Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>', 'name': 'wget',
                        'install_date': '2016-08-30T22:20:15Z', 'description': 'retrieves files from the web',
                        'version': '1.15-1ubuntu1.14.04.2', 'architecture': 'amd64', 'group': 'web', 'source': 'wget'}
        for k in wget_pkg:
            assert k in expected_pkg
            assert wget_pkg[k] == expected_pkg[k]

    @patch('salt.modules.aptpkg.__salt__', {'cmd.run_stdout': MagicMock(return_value='wget: /usr/bin/wget')})
    def test_owner(self):
        '''
        Test - Return the name of the package that owns the file.
        '''
        assert aptpkg.owner('/usr/bin/wget') == 'wget'

    @patch('salt.utils.pkg.clear_rtag', MagicMock())
    @patch('salt.modules.aptpkg.__salt__', {'cmd.run_all': MagicMock(return_value={'retcode': 0,
                                                                                   'stdout': APT_Q_UPDATE}),
                                            'config.get': MagicMock(return_value=False)})
    def test_refresh_db(self):
        '''
        Test - Updates the APT database to latest packages based upon repositories.
        '''
        refresh_db = {
            'http://security.ubuntu.com trusty-security InRelease': True,
            'http://security.ubuntu.com trusty-security/main Sources': True,
            'http://security.ubuntu.com trusty-security/main Translation-en': None,
            'http://security.ubuntu.com trusty-security/main amd64 Packages': True,
            'http://security.ubuntu.com trusty-security/main i386 Packages': True
        }
        assert aptpkg.refresh_db() == refresh_db

    @patch('salt.utils.pkg.clear_rtag', MagicMock())
    @patch('salt.modules.aptpkg.__salt__', {'cmd.run_all': MagicMock(return_value={'retcode': 0,
                                                                                   'stdout': APT_Q_UPDATE_ERROR}),
                                            'config.get': MagicMock(return_value=False)})
    def test_refresh_db_failed(self):
        '''
        Test - Update the APT database using unreachable repositories.
        '''
        with pytest.raises(CommandExecutionError) as err:
            aptpkg.refresh_db(failhard=True)
        assert 'Error getting repos' in str(err)
        assert 'http://security.ubuntu.com trusty InRelease, http://security.ubuntu.com trusty Release.gpg' in str(err)

    def test_autoremove(self):
        '''
        Test - Remove packages not required by another package.
        '''
        with patch('salt.modules.aptpkg.list_pkgs',
                   MagicMock(return_value=PACKAGES)):
            patch_kwargs = {
                '__salt__': {
                    'config.get': MagicMock(return_value=True),
                    'cmd.run': MagicMock(return_value=AUTOREMOVE)
                }
            }
            with patch.multiple(aptpkg, **patch_kwargs):
                self.assertEqual(aptpkg.autoremove(), dict())
                self.assertEqual(aptpkg.autoremove(purge=True), dict())
                self.assertEqual(aptpkg.autoremove(list_only=True), list())
                self.assertEqual(aptpkg.autoremove(list_only=True, purge=True), list())

    @patch('salt.modules.aptpkg._uninstall', MagicMock(return_value=UNINSTALL))
    def test_remove(self):
        '''
        Test - Remove packages.
        '''
        assert aptpkg.remove(name='tmux') == UNINSTALL

    @patch('salt.modules.aptpkg._uninstall', MagicMock(return_value=UNINSTALL))
    def test_purge(self):
        '''
        Test - Remove packages along with all configuration files.
        '''
        assert aptpkg.purge(name='tmux') == UNINSTALL

    @patch('salt.utils.pkg.clear_rtag', MagicMock())
    @patch('salt.modules.aptpkg.list_pkgs', MagicMock(return_value=UNINSTALL))
    @patch.multiple(aptpkg, **{'__salt__': {'config.get': MagicMock(return_value=True),
                                            'cmd.run_all': MagicMock(return_value={'retcode': 0, 'stdout': UPGRADE})}})
    def test_upgrade(self):
        '''
        Test - Upgrades all packages.
        '''
        assert aptpkg.upgrade() == {}
