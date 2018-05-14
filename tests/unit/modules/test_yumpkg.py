# -*- coding: utf-8 -*-

# Import Python Libs
from __future__ import absolute_import
import os

# Import Salt Testing Libs
from salttesting.unit import TestCase, skipIf
from salttesting.mock import (
    MagicMock,
    patch,
    NO_MOCK,
    NO_MOCK_REASON
)

# Import Salt libs
import salt.modules.yumpkg as yumpkg
import salt.modules.pkg_resource as pkg_resource

# Globals
yumpkg.__salt__ = dict()
yumpkg.__grains__ = dict()
yumpkg.__context__ = dict()


RPM_OUT = [
    'python-urlgrabber_|-(none)_|-3.10_|-8.el7_|-noarch_|-(none)_|-1487838471',
    'alsa-lib_|-(none)_|-1.1.1_|-1.el7_|-x86_64_|-(none)_|-1487838475',
    'gnupg2_|-(none)_|-2.0.22_|-4.el7_|-x86_64_|-(none)_|-1487838477',
    'rpm-python_|-(none)_|-4.11.3_|-21.el7_|-x86_64_|-(none)_|-1487838477',
    'pygpgme_|-(none)_|-0.3_|-9.el7_|-x86_64_|-(none)_|-1487838478',
    'yum_|-(none)_|-3.4.3_|-150.el7.centos_|-noarch_|-(none)_|-1487838479',
    'lzo_|-(none)_|-2.06_|-8.el7_|-x86_64_|-(none)_|-1487838479',
    'qrencode-libs_|-(none)_|-3.4.1_|-3.el7_|-x86_64_|-(none)_|-1487838480',
    'ustr_|-(none)_|-1.0.4_|-16.el7_|-x86_64_|-(none)_|-1487838480',
    'shadow-utils_|-2_|-4.1.5.1_|-24.el7_|-x86_64_|-(none)_|-1487838481',
    'util-linux_|-(none)_|-2.23.2_|-33.el7_|-x86_64_|-(none)_|-1487838484',
    'openssh_|-(none)_|-6.6.1p1_|-33.el7_3_|-x86_64_|-(none)_|-1487838485',
    'virt-what_|-(none)_|-1.13_|-8.el7_|-x86_64_|-(none)_|-1487838486',
]

def _add_data(data, key, value):
    data.setdefault(key, []).append(value)


@skipIf(NO_MOCK, NO_MOCK_REASON)
class YumTestCase(TestCase):
    '''
    Test cases for salt.modules.yumpkg
    '''

    @patch.dict(yumpkg.__grains__, {'osarch': 'x86_64', 'os': 'RedHat'})
    @patch.dict(yumpkg.__salt__, {'cmd.run': MagicMock(return_value=os.linesep.join(RPM_OUT))})
    @patch.dict(yumpkg.__salt__, {'cmd.run_all': MagicMock(return_value={'retcode': 0})})
    @patch.dict(yumpkg.__salt__, {'pkg_resource.add_pkg': _add_data})
    @patch.dict(yumpkg.__salt__, {'pkg_resource.parse_targets': MagicMock(return_value=({'python-urlgrabber': '0.0.1'} , 'repository'))})
    @patch.dict(yumpkg.__salt__, {'pkg_resource.format_pkg_list': pkg_resource.format_pkg_list})
    @patch.dict(yumpkg.__salt__, {'config.get': MagicMock()})
    @patch.dict(yumpkg.__salt__, {'lowpkg.version_cmp': MagicMock(return_value=-1)})
    def test_install_pkg(self):
        '''
        Test package installation.

        :return:
        '''
        pkgs = yumpkg.install(name='python-urlgrabber')
        self.assertEqual(pkgs, {})

    @patch.dict(yumpkg.__grains__, {'osarch': 'x86_64', 'os': 'RedHat'})
    @patch.dict(yumpkg.__salt__, {'cmd.run': MagicMock(return_value=os.linesep.join(RPM_OUT))})
    @patch.dict(yumpkg.__salt__, {'cmd.run_all': MagicMock(return_value={'retcode': 0})})
    @patch.dict(yumpkg.__salt__, {'pkg_resource.add_pkg': _add_data})
    @patch.dict(yumpkg.__salt__, {'pkg_resource.parse_targets': MagicMock(return_value=({'python-urlgrabber': '0.0.1'} , 'repository'))})
    @patch.dict(yumpkg.__salt__, {'pkg_resource.format_pkg_list': pkg_resource.format_pkg_list})
    @patch.dict(yumpkg.__salt__, {'config.get': MagicMock()})
    @patch.dict(yumpkg.__salt__, {'lowpkg.version_cmp': MagicMock(return_value=-1)})
    def test_install_pkg_with_diff_attr(self):
        '''
        Test package installation with diff_attr.

        :return:
        '''
        pkgs = yumpkg.install(name='python-urlgrabber', diff_attr=['version', 'epoch', 'release', 'arch'])
        self.assertEqual(pkgs, {})

    @patch.dict(yumpkg.__grains__, {'osarch': 'x86_64'})
    @patch.dict(yumpkg.__salt__, {'cmd.run': MagicMock(return_value=os.linesep.join(RPM_OUT))})
    @patch.dict(yumpkg.__salt__, {'pkg_resource.add_pkg': _add_data})
    @patch.dict(yumpkg.__salt__, {'pkg_resource.format_pkg_list': pkg_resource.format_pkg_list})
    @patch.dict(yumpkg.__salt__, {'pkg_resource.stringify': MagicMock()})
    def test_list_pkgs(self):
        '''
        Test packages listing.

        :return:
        '''
        pkgs = yumpkg.list_pkgs(versions_as_list=True)
        for pkg_name, pkg_version in {
            'python-urlgrabber': '3.10-8.el7',
            'alsa-lib': '1.1.1-1.el7',
            'gnupg2': '2.0.22-4.el7',
            'rpm-python': '4.11.3-21.el7',
            'pygpgme': '0.3-9.el7',
            'yum': '3.4.3-150.el7.centos',
            'lzo': '2.06-8.el7',
            'qrencode-libs': '3.4.1-3.el7',
            'ustr': '1.0.4-16.el7',
            'shadow-utils': '2:4.1.5.1-24.el7',
            'util-linux': '2.23.2-33.el7',
            'openssh': '6.6.1p1-33.el7_3',
            'virt-what': '1.13-8.el7'}.items():
            self.assertTrue(pkgs.get(pkg_name))
            self.assertEqual(pkgs[pkg_name], [pkg_version])

    @patch.dict(yumpkg.__grains__, {'osarch': 'x86_64'})
    @patch.dict(yumpkg.__salt__, {'cmd.run': MagicMock(return_value=os.linesep.join(RPM_OUT))})
    @patch.dict(yumpkg.__salt__, {'pkg_resource.add_pkg': _add_data})
    @patch.dict(yumpkg.__salt__, {'pkg_resource.format_pkg_list': pkg_resource.format_pkg_list})
    @patch.dict(yumpkg.__salt__, {'pkg_resource.stringify': MagicMock()})
    def test_list_pkgs_with_attr(self):
        '''
        Test packages listing with the attr parameter

        :return:
        '''
        pkgs = yumpkg.list_pkgs(attr=['epoch', 'release', 'arch', 'install_date_time_t'])
        for pkg_name, pkg_attr in {
            'python-urlgrabber': {
                'version': '3.10',
                'release': '8.el7',
                'arch': 'noarch',
                'install_date_time_t': 1487838471,
            },
            'alsa-lib': {
                'version': '1.1.1',
                'release': '1.el7',
                'arch': 'x86_64',
                'install_date_time_t': 1487838475,
            },
            'gnupg2': {
                'version': '2.0.22',
                'release': '4.el7',
                'arch': 'x86_64',
                'install_date_time_t': 1487838477,
            },
            'rpm-python': {
                'version': '4.11.3',
                'release': '21.el7',
                'arch': 'x86_64',
                'install_date_time_t': 1487838477,
            },
            'pygpgme': {
                'version': '0.3',
                'release': '9.el7',
                'arch': 'x86_64',
                'install_date_time_t': 1487838478,
            },
            'yum': {
                'version': '3.4.3',
                'release': '150.el7.centos',
                'arch': 'noarch',
                'install_date_time_t': 1487838479,
            },
            'lzo': {
                'version': '2.06',
                'release': '8.el7',
                'arch': 'x86_64',
                'install_date_time_t': 1487838479,
            },
            'qrencode-libs': {
                'version': '3.4.1',
                'release': '3.el7',
                'arch': 'x86_64',
                'install_date_time_t': 1487838480,
            },
            'ustr': {
                'version': '1.0.4',
                'release': '16.el7',
                'arch': 'x86_64',
                'install_date_time_t': 1487838480,
            },
            'shadow-utils': {
                'epoch': '2',
                'version': '4.1.5.1',
                'release': '24.el7',
                'arch': 'x86_64',
                'install_date_time_t': 1487838481,
            },
            'util-linux': {
                'version': '2.23.2',
                'release': '33.el7',
                'arch': 'x86_64',
                'install_date_time_t': 1487838484,
            },
            'openssh': {
                'version': '6.6.1p1',
                'release': '33.el7_3',
                'arch': 'x86_64',
                'install_date_time_t': 1487838485,
            },
            'virt-what': {
                'version': '1.13',
                'release': '8.el7',
                'install_date_time_t': 1487838486,
                'arch': 'x86_64',
            }}.items():
            self.assertTrue(pkgs.get(pkg_name))
            self.assertEqual(pkgs[pkg_name], [pkg_attr])

    def test_info_installed_with_all_versions(self):
        '''
        Test the return information of all versions for the named package(s), installed on the system.

        :return:
        '''
        run_out = {
            'virgo-dummy': [
                {'build_date': '2015-07-09T10:55:19Z',
                 'vendor': 'openSUSE Build Service',
                 'description': 'This is the Virgo dummy package used for testing SUSE Manager',
                 'license': 'GPL-2.0', 'build_host': 'sheep05', 'url': 'http://www.suse.com',
                 'build_date_time_t': 1436432119, 'relocations': '(not relocatable)',
                 'source_rpm': 'virgo-dummy-1.0-1.1.src.rpm', 'install_date': '2016-02-23T16:31:57Z',
                 'install_date_time_t': 1456241517, 'summary': 'Virgo dummy package', 'version': '1.0',
                 'signature': 'DSA/SHA1, Thu Jul  9 08:55:33 2015, Key ID 27fa41bd8a7c64f9',
                 'release': '1.1', 'group': 'Applications/System', 'arch': 'i686', 'size': '17992'},
                {'build_date': '2015-07-09T10:15:19Z',
                 'vendor': 'openSUSE Build Service',
                 'description': 'This is the Virgo dummy package used for testing SUSE Manager',
                 'license': 'GPL-2.0', 'build_host': 'sheep05', 'url': 'http://www.suse.com',
                 'build_date_time_t': 1436432119, 'relocations': '(not relocatable)',
                 'source_rpm': 'virgo-dummy-1.0-1.1.src.rpm', 'install_date': '2016-02-23T16:31:57Z',
                 'install_date_time_t': 14562415127, 'summary': 'Virgo dummy package', 'version': '1.0',
                 'signature': 'DSA/SHA1, Thu Jul  9 08:55:33 2015, Key ID 27fa41bd8a7c64f9',
                 'release': '1.1', 'group': 'Applications/System', 'arch': 'x86_64', 'size': '13124'}
            ],
            'libopenssl1_0_0': [
                {'build_date': '2015-11-04T23:20:34Z', 'vendor': 'SUSE LLC <https://www.suse.com/>',
                 'description': 'The OpenSSL Project is a collaborative effort.',
                 'license': 'OpenSSL', 'build_host': 'sheep11', 'url': 'https://www.openssl.org/',
                 'build_date_time_t': 1446675634, 'relocations': '(not relocatable)',
                 'source_rpm': 'openssl-1.0.1i-34.1.src.rpm', 'install_date': '2016-02-23T16:31:35Z',
                 'install_date_time_t': 1456241495, 'summary': 'Secure Sockets and Transport Layer Security',
                 'version': '1.0.1i', 'signature': 'RSA/SHA256, Wed Nov  4 22:21:34 2015, Key ID 70af9e8139db7c82',
                 'release': '34.1', 'group': 'Productivity/Networking/Security', 'packager': 'https://www.suse.com/',
                 'arch': 'x86_64', 'size': '2576912'}
            ]
        }
        with patch.dict(yumpkg.__salt__, {'lowpkg.info': MagicMock(return_value=run_out)}):
            installed = yumpkg.info_installed(all_versions=True)
            # Test overall products length
            self.assertEqual(len(installed), 2)

            # Test multiple versions for the same package
            for pkg_name, pkg_info_list in installed.items():
                self.assertEqual(len(pkg_info_list), 2 if pkg_name == "virgo-dummy" else 1)
                for info in pkg_info_list:
                    self.assertTrue(info['arch'] in ('x86_64', 'i686'))
