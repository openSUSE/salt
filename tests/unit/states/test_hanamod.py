
# -*- coding: utf-8 -*-
'''
    :codeauthor: Xabier Arbulu Insausti <xarbulu@suse.com>
'''
# Import Python libs
from __future__ import absolute_import, unicode_literals, print_function

from salt import exceptions

# Import Salt Testing Libs
from tests.support.mixins import LoaderModuleMockMixin
from tests.support.unit import skipIf, TestCase
from tests.support import mock
from tests.support.mock import (
    NO_MOCK,
    NO_MOCK_REASON,
    MagicMock,
    patch
)

# Import Salt Libs
import salt.states.hanamod as hanamod


@skipIf(NO_MOCK, NO_MOCK_REASON)
class HanamodTestCase(TestCase, LoaderModuleMockMixin):
    '''
    Test cases for salt.states.hanamod
    '''
    def setup_loader_modules(self):
        return {hanamod: {'__opts__': {'test': False}}}

    # 'installed' function tests

    def test_installed_installed(self):
        '''
        Test to check installed when hana is already installed
        '''

        ret = {'name': 'prd',
               'changes': {},
               'result': True,
               'comment': 'HANA is already installed'}

        mock_installed = MagicMock(return_value=True)
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed}):
            assert hanamod.installed(
                'prd', '00', 'pass', '/software', 'root', 'pass') == ret

    def test_installed_test(self):
        '''
        Test to check installed in test mode
        '''

        ret = {'name': 'prd',
               'changes': {'sid': 'prd'},
               'result': None,
               'comment': '{} would be installed'.format('prd')}

        mock_installed = MagicMock(return_value=False)
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed}):
            with patch.dict(hanamod.__opts__, {'test': True}):
                assert hanamod.installed(
                    'prd', '00', 'pass', '/software', 'root', 'pass') == ret

    def test_installed_config_file(self):
        '''
        Test to check installed when config file is imported
        '''

        ret = {'name': 'prd',
               'changes': {'sid': 'prd', 'config_file': 'hana.conf'},
               'result': True,
               'comment': 'HANA installed'}

        mock_installed = MagicMock(return_value=False)
        mock_cp = MagicMock()
        mock_update = MagicMock(return_value='hana_updated.conf')
        mock_install = MagicMock()
        mock_remove = MagicMock()
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed,
                                           'cp.get_file': mock_cp,
                                           'hana.update_conf_file': mock_update,
                                           'hana.install': mock_install,
                                           'file.remove': mock_remove}):
            assert hanamod.installed(
                'prd', '00', 'pass', '/software',
                'root', 'pass', config_file='hana.conf',
                extra_parameters=[{'hostname': 'hana01'}]) == ret

            mock_cp.assert_called_once_with(
                path='hana.conf',
                dest=hanamod.TMP_CONFIG_FILE)
            mock_update.assert_called_once_with(
                conf_file=hanamod.TMP_CONFIG_FILE,
                extra_parameters={u'hostname': u'hana01'})
            mock_install.assert_called_once_with(
                software_path='/software',
                conf_file='hana_updated.conf',
                root_user='root',
                root_password='pass')
            mock_remove.assert_has_calls([
                mock.call(hanamod.TMP_CONFIG_FILE),
                mock.call('{}.xml'.format(hanamod.TMP_CONFIG_FILE))
            ])

    def test_installed_dump(self):
        '''
        Test to check installed when new config file is created
        '''

        ret = {'name': 'prd',
               'changes': {'sid': 'prd', 'config_file': 'new'},
               'result': True,
               'comment': 'HANA installed'}

        mock_installed = MagicMock(return_value=False)
        mock_create = MagicMock(return_value='hana_created.conf')
        mock_update = MagicMock(return_value='hana_updated.conf')
        mock_install = MagicMock()
        mock_remove = MagicMock()
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed,
                                           'hana.create_conf_file': mock_create,
                                           'hana.update_conf_file': mock_update,
                                           'hana.install': mock_install,
                                           'file.remove': mock_remove}):
            assert hanamod.installed(
                'prd', '00', 'pass', '/software',
                'root', 'pass',
                system_user_password='sys_pass',
                sapadm_password='pass',
                extra_parameters=[{'hostname': 'hana01'}]) == ret

            mock_create.assert_called_once_with(
                software_path='/software',
                conf_file=hanamod.TMP_CONFIG_FILE,
                root_user='root',
                root_password='pass')
            mock_update.assert_has_calls([
                mock.call(
                    conf_file='hana_created.conf', sid='PRD', number='00',
                    password='pass', root_user='root', root_password='pass',
                    sapadm_password='pass', system_user_password='sys_pass'),
                mock.call(
                    conf_file='hana_updated.conf',
                    extra_parameters={u'hostname': u'hana01'})
            ])

            mock_install.assert_called_once_with(
                software_path='/software',
                conf_file='hana_updated.conf',
                root_user='root',
                root_password='pass')
            mock_remove.assert_has_calls([
                mock.call(hanamod.TMP_CONFIG_FILE),
                mock.call('{}.xml'.format(hanamod.TMP_CONFIG_FILE))
            ])

    def test_installed_invalid_params(self):
        '''
        Test to check installed when install fails
        '''

        ret = {'name': 'prd',
               'changes': {},
               'result': False,
               'comment': 'If config_file is not provided '
                          'system_user_password and sapadm_password are mandatory'}

        mock_installed = MagicMock(return_value=False)

        mock_remove = MagicMock()
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed,
                                           'file.remove': mock_remove}):
            assert hanamod.installed(
                'prd', '00', 'pass', '/software',
                'root', 'pass') == ret

            mock_remove.assert_has_calls([
                mock.call(hanamod.TMP_CONFIG_FILE),
                mock.call('{}.xml'.format(hanamod.TMP_CONFIG_FILE))
            ])

    def test_installed_error(self):
        '''
        Test to check installed when install fails
        '''

        ret = {'name': 'prd',
               'changes': {'config_file': 'new'},
               'result': False,
               'comment': 'hana command error'}

        mock_installed = MagicMock(return_value=False)
        mock_create = MagicMock(return_value='hana_created.conf')
        mock_update = MagicMock(return_value='hana_updated.conf')
        mock_install = MagicMock(
            side_effect=exceptions.CommandExecutionError('hana command error'))
        mock_remove = MagicMock()
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed,
                                           'hana.create_conf_file': mock_create,
                                           'hana.update_conf_file': mock_update,
                                           'hana.install': mock_install,
                                           'file.remove': mock_remove}):
            assert hanamod.installed(
                'prd', '00', 'pass', '/software',
                'root', 'pass',
                sapadm_password='pass',
                system_user_password='sys_pass') == ret

            mock_create.assert_called_once_with(
                software_path='/software',
                conf_file=hanamod.TMP_CONFIG_FILE,
                root_user='root',
                root_password='pass')
            mock_update.assert_called_once_with(
                    conf_file='hana_created.conf', sid='PRD', number='00',
                    password='pass', root_user='root', root_password='pass',
                    sapadm_password='pass', system_user_password='sys_pass')

            mock_install.assert_called_once_with(
                software_path='/software',
                conf_file='hana_updated.conf',
                root_user='root',
                root_password='pass')
            mock_remove.assert_has_calls([
                mock.call(hanamod.TMP_CONFIG_FILE),
                mock.call('{}.xml'.format(hanamod.TMP_CONFIG_FILE))
            ])

    # 'uninstalled' function tests

    def test_uninstalled_uinstalled(self):
        '''
        Test to check uninstalled when hana is already installed
        '''

        ret = {'name': 'prd',
               'changes': {},
               'result': True,
               'comment': 'HANA already not installed'}

        mock_installed = MagicMock(return_value=False)
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed}):
            assert hanamod.uninstalled(
                'prd', '00', 'pass', 'root', 'pass') == ret

    def test_uninstalled_test(self):
        '''
        Test to check uninstalled in test mode
        '''

        ret = {'name': 'prd',
               'changes': {'sid': 'prd'},
               'result': None,
               'comment': '{} would be uninstalled'.format('prd')}

        mock_installed = MagicMock(return_value=True)
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed}):
            with patch.dict(hanamod.__opts__, {'test': True}):
                assert hanamod.uninstalled(
                    'prd', '00', 'pass', 'root', 'pass') == ret

    def test_uninstalled(self):
        '''
        Test to check uninstalled when hana is installed
        '''

        ret = {'name': 'prd',
               'changes': {'sid': 'prd'},
               'result': True,
               'comment': 'HANA uninstalled'}

        mock_is_installed = MagicMock(return_value=True)
        mock_uninstall = MagicMock()
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_is_installed,
                                           'hana.uninstall': mock_uninstall}):
            assert hanamod.uninstalled(
                'prd', '00', 'pass', 'root', 'pass',
                installation_folder='/hana') == ret
            mock_uninstall.assert_called_once_with(
                root_user='root', root_password='pass',
                sid='prd', inst='00', password='pass',
                installation_folder='/hana')

    def test_uninstalled_error(self):
        '''
        Test to check uninstalled when hana uninstall method fails
        '''

        ret = {'name': 'prd',
               'changes': {},
               'result': False,
               'comment': 'hana command error'}

        mock_installed = MagicMock(return_value=True)
        mock_uninstall = MagicMock(
            side_effect=exceptions.CommandExecutionError('hana command error'))
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed,
                                           'hana.uninstall': mock_uninstall}):
            assert hanamod.uninstalled(
                'prd', '00', 'pass', 'root', 'pass',
                installation_folder='/hana') == ret
            mock_uninstall.assert_called_once_with(
                root_user='root', root_password='pass',
                sid='prd', inst='00', password='pass',
                installation_folder='/hana')

    # 'sr_primary_enabled' function tests

    def test_sr_primary_enabled_not_installed(self):
        '''
        Test to check sr_primary_enabled when hana is not installed
        '''
        name = 'SITE1'

        ret = {'name': name,
               'changes': {},
               'result': False,
               'comment': 'HANA is not installed properly with the provided data'}

        mock_installed = MagicMock(return_value=False)
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed}):
            assert hanamod.sr_primary_enabled(
                name, 'pdr', '00', 'pass') == ret

    @patch('salt.modules.hanamod.hana.SrStates.PRIMARY')
    def test_sr_primary_enabled(self, mock_primary):
        '''
        Test to check sr_primary_enabled when hana is already set as primary
        node
        '''
        name = 'SITE1'

        ret = {'name': name,
               'changes': {},
               'result': True,
               'comment': 'HANA node already set as primary and running'}

        mock_installed = MagicMock(return_value=True)
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed}):
            mock_running = MagicMock(return_value=True)
            mock_state = MagicMock(return_value=mock_primary)

            with patch.dict(hanamod.__salt__, {'hana.is_running': mock_running,
                                               'hana.get_sr_state': mock_state}):
                assert hanamod.sr_primary_enabled(
                    name, 'pdr', '00', 'pass') == ret

    def test_sr_primary_enabled_test(self):
        '''
        Test to check sr_primary_enabled in test mode
        '''
        name = 'SITE1'

        ret = {'name': name,
               'changes': {
                   'primary': name,
                   'backup': None,
                   'userkey': None
               },
               'result': None,
               'comment': '{} would be enabled as a primary node'.format(name)}

        mock_installed = MagicMock(return_value=True)
        mock_running = MagicMock(return_value=True)
        mock_state = MagicMock()
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed,
                                           'hana.is_running': mock_running,
                                           'hana.get_sr_state': mock_state}):
            with patch.dict(hanamod.__opts__, {'test': True}):
                assert hanamod.sr_primary_enabled(
                    name, 'pdr', '00', 'pass') == ret

    def test_sr_primary_enabled_basic(self):
        '''
        Test to check sr_primary_enabled when hana is already set as primary
        node with basic setup
        '''
        name = 'SITE1'

        ret = {'name': name,
               'changes': {
                   'primary': name
               },
               'result': True,
               'comment': 'HANA node set as {}'.format('PRIMARY')}

        mock_installed = MagicMock(return_value=True)
        mock_running = MagicMock(return_value=True)
        state = MagicMock()
        state_primary = MagicMock()
        state_primary.name = 'PRIMARY'
        mock_state = MagicMock(side_effect=[state, state_primary])
        mock_enable = MagicMock()
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed,
                                           'hana.is_running': mock_running,
                                           'hana.get_sr_state': mock_state,
                                           'hana.sr_enable_primary': mock_enable}):
            assert hanamod.sr_primary_enabled(
                name, 'pdr', '00', 'pass') == ret
            mock_enable.assert_called_once_with(
                name=name,
                sid='pdr',
                inst='00',
                password='pass')

    def test_sr_primary_enabled_complex(self):
        '''
        Test to check sr_primary_enabled when hana is already set as primary
        node with complex setup (backup and userkey created)
        '''
        name = 'SITE1'

        ret = {'name': name,
               'changes': {
                   'primary': name,
                   'userkey': 'key',
                   'backup': 'file'
               },
               'result': True,
               'comment': 'HANA node set as {}'.format('PRIMARY')}

        userkey = [
            {'key': 'key'},
            {'environment': 'env'},
            {'user': 'user'},
            {'password': 'password'},
            {'database': 'database'}
        ]

        backup = [
            {'user': 'user'},
            {'password': 'password'},
            {'database': 'database'},
            {'file': 'file'}
        ]

        mock_installed = MagicMock(return_value=True)
        mock_running = MagicMock(return_value=False)
        state = MagicMock()
        state_primary = MagicMock()
        state_primary.name = 'PRIMARY'
        mock_state = MagicMock(side_effect=[state, state_primary])
        mock_start = MagicMock()
        mock_enable = MagicMock()
        mock_userkey = MagicMock()
        mock_backup = MagicMock()
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed,
                                           'hana.is_running': mock_running,
                                           'hana.get_sr_state': mock_state,
                                           'hana.start': mock_start,
                                           'hana.sr_enable_primary': mock_enable,
                                           'hana.create_user_key': mock_userkey,
                                           'hana.create_backup': mock_backup}):
            assert hanamod.sr_primary_enabled(
                name, 'pdr', '00', 'pass', userkey=userkey, backup=backup) == ret
            mock_start.assert_called_once_with(
                sid='pdr',
                inst='00',
                password='pass')
            mock_enable.assert_called_once_with(
                name=name,
                sid='pdr',
                inst='00',
                password='pass')
            mock_userkey.assert_called_once_with(
                key='key',
                environment='env',
                user='user',
                user_password='password',
                database='database',
                sid='pdr',
                inst='00',
                password='pass')
            mock_backup.assert_called_once_with(
                user_key='user',
                user_password='password',
                database='database',
                backup_name='file',
                sid='pdr',
                inst='00',
                password='pass')

    def test_sr_primary_enabled_error(self):
        '''
        Test to check sr_primary_enabled when hana is already set as primary
        node and some hana command fail
        '''
        name = 'SITE1'

        ret = {'name': name,
               'changes': {},
               'result': False,
               'comment': 'hana command error'}

        mock_installed = MagicMock(return_value=True)
        mock_running = MagicMock(return_value=False)
        state = MagicMock()
        state_primary = MagicMock()
        state_primary.name = 'PRIMARY'
        mock_state = MagicMock(side_effect=[state, state_primary])
        mock_start = MagicMock()
        mock_enable = MagicMock(
            side_effect=exceptions.CommandExecutionError('hana command error'))
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed,
                                           'hana.is_running': mock_running,
                                           'hana.get_sr_state': mock_state,
                                           'hana.start': mock_start,
                                           'hana.sr_enable_primary': mock_enable}):
            assert hanamod.sr_primary_enabled(
                name, 'pdr', '00', 'pass') == ret
            mock_start.assert_called_once_with(
                sid='pdr',
                inst='00',
                password='pass')
            mock_enable.assert_called_once_with(
                name=name,
                sid='pdr',
                inst='00',
                password='pass')

    # 'sr_secondary_registered' function tests

    def test_sr_secondary_registered_not_installed(self):
        '''
        Test to check sr_secondary_registered when hana is not installed
        '''
        name = 'SITE2'

        ret = {'name': name,
               'changes': {},
               'result': False,
               'comment': 'HANA is not installed properly with the provided data'}

        mock_installed = MagicMock(return_value=False)
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed}):
            assert hanamod.sr_secondary_registered(
                name, 'pdr', '00', 'pass', 'hana01', '00', 'sync',
                'logreplay') == ret

    @patch('salt.modules.hanamod.hana.SrStates.SECONDARY')
    def test_sr_secondary_registered(self, mock_secondary):
        '''
        Test to check sr_secondary_registered when hana is already set as secondary
        node
        '''
        name = 'SITE2'

        ret = {'name': name,
               'changes': {},
               'result': True,
               'comment': 'HANA node already set as secondary and running'}

        mock_installed = MagicMock(return_value=True)
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed}):
            mock_running = MagicMock(return_value=True)
            mock_state = MagicMock(return_value=mock_secondary)

            with patch.dict(hanamod.__salt__, {'hana.is_running': mock_running,
                                               'hana.get_sr_state': mock_state}):
                assert hanamod.sr_secondary_registered(
                    name, 'pdr', '00', 'pass', 'hana01', '00', 'sync',
                    'logreplay') == ret

    def test_sr_secondary_registered_test(self):
        '''
        Test to check sr_secondary_registered when hana is already set as secondary
        node in test mode
        '''
        name = 'SITE2'

        ret = {'name': name,
               'changes': {
                   'secondary': name
               },
               'result': None,
               'comment': '{} would be registered as a secondary node'.format(name)}

        mock_installed = MagicMock(return_value=True)
        mock_running = MagicMock(return_value=True)
        state = MagicMock()
        mock_state = MagicMock(return_value=state)
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed,
                                           'hana.is_running': mock_running,
                                           'hana.get_sr_state': mock_state}):
            with patch.dict(hanamod.__opts__, {'test': True}):
                assert hanamod.sr_secondary_registered(
                    name, 'pdr', '00', 'pass', 'hana01', '00', 'sync',
                    'logreplay') == ret

    def test_sr_secondary_registered_basic(self):
        '''
        Test to check sr_secondary_registered when hana is already set as secondary
        node with basic setup
        '''
        name = 'SITE2'

        ret = {'name': name,
               'changes': {
                   'secondary': name
               },
               'result': True,
               'comment': 'HANA node set as {}'.format('SECONDARY')}

        mock_installed = MagicMock(return_value=True)
        mock_running = MagicMock(return_value=True)
        state = MagicMock()
        state_secondary = MagicMock()
        state_secondary.name = 'SECONDARY'
        mock_state = MagicMock(side_effect=[state, state_secondary])
        mock_stop = MagicMock()
        mock_start = MagicMock()
        mock_register = MagicMock()
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed,
                                           'hana.is_running': mock_running,
                                           'hana.get_sr_state': mock_state,
                                           'hana.stop': mock_stop,
                                           'hana.start': mock_start,
                                           'hana.sr_register_secondary': mock_register}):
            assert hanamod.sr_secondary_registered(
                name, 'hana01', '00', 'sync',
                'logreplay', 'pdr', '00', 'pass') == ret
            mock_stop.assert_called_once_with(
                sid='pdr',
                inst='00',
                password='pass')
            mock_start.assert_called_once_with(
                sid='pdr',
                inst='00',
                password='pass')
            mock_register.assert_called_once_with(
                name=name,
                remote_host='hana01',
                remote_instance='00',
                replication_mode='sync',
                operation_mode='logreplay',
                sid='pdr',
                inst='00',
                password='pass')

    def test_sr_secondary_registered_error(self):
        '''
        Test to check sr_secondary_registered when hana is already set as secondary
        node and some hana command fail
        '''
        name = 'SITE2'

        ret = {'name': name,
               'changes': {},
               'result': False,
               'comment': 'hana command error'}

        mock_installed = MagicMock(return_value=True)
        mock_running = MagicMock(return_value=False)
        state = MagicMock()
        mock_state = MagicMock(return_value=state)
        mock_register = MagicMock(
            side_effect=exceptions.CommandExecutionError('hana command error'))
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed,
                                           'hana.is_running': mock_running,
                                           'hana.get_sr_state': mock_state,
                                           'hana.sr_register_secondary': mock_register}):
            assert hanamod.sr_secondary_registered(
                name, 'hana01', '00', 'sync',
                'logreplay', 'pdr', '00', 'pass') == ret
            mock_register.assert_called_once_with(
                name=name,
                remote_host='hana01',
                remote_instance='00',
                replication_mode='sync',
                operation_mode='logreplay',
                sid='pdr',
                inst='00',
                password='pass')

    # 'sr_clean' function tests

    def test_sr_clean_not_installed(self):
        '''
        Test to check sr_clean when hana is not installed
        '''
        name = 'SITE1'

        ret = {'name': name,
               'changes': {},
               'result': False,
               'comment': 'HANA is not installed properly with the provided data'}

        mock_installed = MagicMock(return_value=False)
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed}):
            assert hanamod.sr_clean(
                name, True, 'pdr', '00', 'pass') == ret

    @patch('salt.modules.hanamod.hana.SrStates.DISABLED')
    def test_sr_clean(self, mock_disabled):
        '''
        Test to check sr_clean when hana is already disabled
        node
        '''
        name = 'SITE1'

        ret = {'name': name,
               'changes': {},
               'result': True,
               'comment': 'HANA node already clean'}

        mock_disabled.name = 'DISABLED'
        mock_installed = MagicMock(return_value=True)
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed}):
            mock_running = MagicMock(return_value=True)
            mock_state = MagicMock(return_value=mock_disabled)

            with patch.dict(hanamod.__salt__, {'hana.is_running': mock_running,
                                               'hana.get_sr_state': mock_state}):
                assert hanamod.sr_clean(
                    name, True, 'pdr', '00', 'pass') == ret

    @patch('salt.modules.hanamod.hana.SrStates.DISABLED')
    def test_sr_clean_test(self, mock_disabled):
        '''
        Test to check sr_clean when hana is not disabled
        node in test mode
        '''
        name = 'SITE1'

        ret = {'name': name,
               'changes': {
                   'disabled': name
               },
               'result': None,
               'comment': '{} would be clean'.format(name)}

        mock_disabled.name = 'DISABLED'
        mock_installed = MagicMock(return_value=True)
        mock_running = MagicMock(return_value=True)
        state = MagicMock()
        mock_state = MagicMock(return_value=state)
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed,
                                           'hana.is_running': mock_running,
                                           'hana.get_sr_state': mock_state}):
            with patch.dict(hanamod.__opts__, {'test': True}):
                assert hanamod.sr_clean(
                    name, True, 'pdr', '00', 'pass') == ret

    @patch('salt.modules.hanamod.hana.SrStates.DISABLED')
    def test_sr_clean_basic(self, mock_disabled):
        '''
        Test to check sr_clean when hana is already set as secondary
        node with basic setup
        '''
        name = 'SITE1'

        ret = {'name': name,
               'changes': {
                   'disabled': name
               },
               'result': True,
               'comment': 'HANA node set as {}'.format('DISABLED')}

        mock_disabled.name = 'DISABLED'
        mock_installed = MagicMock(return_value=True)
        mock_running = MagicMock(return_value=True)
        state = MagicMock()
        state_disabled = MagicMock()
        state_disabled.name = 'DISABLED'
        mock_state = MagicMock(side_effect=[state, state_disabled])
        mock_stop = MagicMock()
        mock_clean = MagicMock()
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_installed,
                                           'hana.is_running': mock_running,
                                           'hana.get_sr_state': mock_state,
                                           'hana.stop': mock_stop,
                                           'hana.sr_cleanup': mock_clean}):
            assert hanamod.sr_clean(
                name, True, 'pdr', '00', 'pass') == ret
            mock_stop.assert_called_once_with(
                sid='pdr',
                inst='00',
                password='pass')
            mock_clean.assert_called_once_with(
                force=True,
                sid='pdr',
                inst='00',
                password='pass')

    @patch('salt.modules.hanamod.hana.SrStates.DISABLED')
    def test_sr_clean_error(self, mock_disabled):
        '''
        Test to check sr_clean when hana is already not disabled
        node and some hana command fail
        '''
        name = 'SITE1'

        ret = {'name': name,
               'changes': {},
               'result': False,
               'comment': 'hana command error'}

        mock_disabled.name = 'DISABLED'
        mock_insatlled = MagicMock(return_value=True)
        mock_running = MagicMock(return_value=False)
        state = MagicMock()
        mock_state = MagicMock(return_value=state)
        mock_clean = MagicMock(
            side_effect=exceptions.CommandExecutionError('hana command error'))
        with patch.dict(hanamod.__salt__, {'hana.is_installed': mock_insatlled,
                                           'hana.is_running': mock_running,
                                           'hana.get_sr_state': mock_state,
                                           'hana.sr_cleanup': mock_clean}):
            assert hanamod.sr_clean(
                name, True, 'pdr', '00', 'pass') == ret
            mock_clean.assert_called_once_with(
                force=True,
                sid='pdr',
                inst='00',
                password='pass')
