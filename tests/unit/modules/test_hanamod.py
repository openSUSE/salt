
# -*- coding: utf-8 -*-
'''
    :codeauthor: Xabier Arbulu Insausti <xarbulu@suse.com>
'''

# Import Python Libs
from __future__ import absolute_import, print_function, unicode_literals

from salt import exceptions

# Import Salt Testing Libs
from tests.support.mixins import LoaderModuleMockMixin
from tests.support.unit import TestCase, skipIf
from tests.support import mock
from tests.support.mock import (
    MagicMock,
    patch,
    NO_MOCK,
    NO_MOCK_REASON
)

# Import Salt Libs
import salt.modules.hanamod as hanamod


@skipIf(NO_MOCK, NO_MOCK_REASON)
class HanaModuleTest(TestCase, LoaderModuleMockMixin):
    '''
    This class contains a set of functions that test salt.modules.hana.
    '''

    def setup_loader_modules(self):
        return {hanamod: {}}

    @patch('salt.modules.hanamod.hana.HanaInstance')
    def test_init_return(self, mock_hana):
        '''
        Test _init method
        '''
        mock_hana_inst = MagicMock()
        mock_hana.return_value = mock_hana_inst
        hana_inst = hanamod._init('prd', '00', 'pass')
        mock_hana.assert_called_once_with('prd', '00', 'pass')
        self.assertEqual(mock_hana_inst, hana_inst)

    @patch('salt.modules.hanamod.hana.HanaInstance')
    def test_init_return_conf(self, mock_hana):
        '''
        Test _init method
        '''
        mock_hana_inst = MagicMock()
        mock_hana.return_value = mock_hana_inst
        mock_config = MagicMock(side_effect=[
            'conf_sid',
            'conf_inst',
            'conf_password'
        ])

        with patch.dict(hanamod.__salt__, {'config.option': mock_config}):
            hana_inst = hanamod._init()
            mock_hana.assert_called_once_with(
                'conf_sid', 'conf_inst', 'conf_password')
            self.assertEqual(mock_hana_inst, hana_inst)
            mock_config.assert_has_calls([
                mock.call('hana.sid', None),
                mock.call('hana.inst', None),
                mock.call('hana.password', None)
            ])

    @patch('salt.modules.hanamod.hana.HanaInstance')
    def test_init_raise(self, mock_hana):
        '''
        Test _init method
        '''
        mock_hana.side_effect = TypeError('error')
        with self.assertRaises(exceptions.SaltInvocationError) as err:
            hanamod._init('prd', '00', 'pass')
        mock_hana.assert_called_once_with('prd', '00', 'pass')
        self.assertTrue('error' in str(err.exception))

    def test_is_installed_return_true(self):
        '''
        Test is_installed method
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.is_installed.return_value = True
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            self.assertTrue(hanamod.is_installed('prd', '00', 'pass'))
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.is_installed.assert_called_once_with()

    def test_is_installed_return_false(self):
        '''
        Test is_installed method
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.is_installed.return_value = False
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            self.assertFalse(hanamod.is_installed('prd', '00', 'pass'))
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.is_installed.assert_called_once_with()

    @patch('salt.modules.hanamod.hana.HanaInstance')
    def test_create_conf_file_return(self, mock_hana):
        '''
        Test create_conf_file method - return
        '''
        mock_hana.create_conf_file.return_value = 'hana.conf'
        conf_file = hanamod.create_conf_file(
            'software_path', 'hana.conf', 'root', 'root')
        self.assertEqual(u'hana.conf', conf_file)
        mock_hana.create_conf_file.assert_called_once_with(
            'software_path', 'hana.conf', 'root', 'root')

    @patch('salt.modules.hanamod.hana.HanaInstance')
    def test_create_conf_file_raise(self, mock_hana):
        '''
        Test create_conf_file method - raise
        '''
        mock_hana.create_conf_file.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        with self.assertRaises(exceptions.CommandExecutionError) as err:
            hanamod.create_conf_file('software_path', 'hana.conf', 'root', 'root')
        mock_hana.create_conf_file.assert_called_once_with(
            'software_path', 'hana.conf', 'root', 'root')
        self.assertTrue('hana error' in str(err.exception))

    @patch('salt.modules.hanamod.hana.HanaInstance')
    def test_update_conf_file_return(self, mock_hana):
        '''
        Test update_conf_file method - return
        '''
        mock_hana.update_conf_file.return_value = 'hana.conf'
        conf_file = hanamod.update_conf_file(
            'hana.conf', sid='sid', number='00')
        self.assertEqual(u'hana.conf', conf_file)
        mock_hana.update_conf_file.assert_called_once_with(
            'hana.conf', sid='sid', number='00')

    @patch('salt.modules.hanamod.hana.HanaInstance')
    def test_update_conf_file_raise(self, mock_hana):
        '''
        Test update_conf_file method - raise
        '''
        mock_hana.update_conf_file.side_effect = IOError('hana error')
        with self.assertRaises(exceptions.CommandExecutionError) as err:
            hanamod.update_conf_file('hana.conf', sid='sid', number='00')
        mock_hana.update_conf_file.assert_called_once_with(
            'hana.conf', sid='sid', number='00')
        self.assertTrue('hana error' in str(err.exception))

    @patch('salt.modules.hanamod.hana.HanaInstance')
    def test_install_return(self, mock_hana):
        '''
        Test install method - return
        '''
        mock_hana.install.return_value = 'hana.conf'
        hanamod.install(
            'software_path', 'hana.conf', 'root', 'root')
        mock_hana.install.assert_called_once_with(
            'software_path', 'hana.conf', 'root', 'root')

    @patch('salt.modules.hanamod.hana.HanaInstance')
    def test_install_raise(self, mock_hana):
        '''
        Test install method - raise
        '''
        mock_hana.install.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        with self.assertRaises(exceptions.CommandExecutionError) as err:
            hanamod.install('software_path', 'hana.conf', 'root', 'root')
        mock_hana.install.assert_called_once_with(
            'software_path', 'hana.conf', 'root', 'root')
        self.assertTrue('hana error' in str(err.exception))

    def test_uninstall_return(self):
        '''
        Test uninstall method - return
        '''
        mock_hana_inst = MagicMock()
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            hanamod.uninstall('root', 'pass', '/hana', 'prd', '00', 'pass')
            mock_hana.assert_called_once_with(
                'prd', '00', 'pass')
            mock_hana_inst.uninstall.assert_called_once_with(
                'root', 'pass', installation_folder='/hana')

    def test_uninstall_return_default(self):
        '''
        Test uninstall method - return
        '''
        mock_hana_inst = MagicMock()
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            hanamod.uninstall('root', 'pass', None, 'prd', '00', 'pass')
            mock_hana.assert_called_once_with(
                'prd', '00', 'pass')
            mock_hana_inst.uninstall.assert_called_once_with('root', 'pass')

    def test_uninstall_raise(self):
        '''
        Test uninstall method - raise
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.uninstall.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            with self.assertRaises(exceptions.CommandExecutionError) as err:
                hanamod.uninstall('root', 'pass', None, 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.uninstall.assert_called_once_with('root', 'pass')
            self.assertTrue('hana error' in str(err.exception))

    def test_is_running_return_true(self):
        '''
        Test is_running method
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.is_running.return_value = True
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            self.assertTrue(hanamod.is_running('prd', '00', 'pass'))
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.is_running.assert_called_once_with()

    def test_is_running_return_false(self):
        '''
        Test is_running method
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.is_running.return_value = False
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            self.assertFalse(hanamod.is_running('prd', '00', 'pass'))
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.is_running.assert_called_once_with()

    def test_get_version_return(self):
        '''
        Test get_version method - return
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.get_version.return_value = '1.2.3'
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            self.assertEqual(u'1.2.3', hanamod.get_version('prd', '00', 'pass'))
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.get_version.assert_called_once_with()

    def test_get_version_raise(self):
        '''
        Test get_version method - raise
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.get_version.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            with self.assertRaises(exceptions.CommandExecutionError) as err:
                hanamod.get_version('prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.get_version.assert_called_once_with()
            self.assertTrue('hana error' in str(err.exception))

    def test_start_return(self):
        '''
        Test start method - return
        '''
        mock_hana_inst = MagicMock()
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            hanamod.start('prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.start.assert_called_once_with()

    def test_start_raise(self):
        '''
        Test start method - raise
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.start.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            with self.assertRaises(exceptions.CommandExecutionError) as err:
                hanamod.start('prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.start.assert_called_once_with()
            self.assertTrue('hana error' in str(err.exception))

    def test_stop_return(self):
        '''
        Test stop method - return
        '''
        mock_hana_inst = MagicMock()
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            hanamod.stop('prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.stop.assert_called_once_with()

    def test_stop_raise(self):
        '''
        Test stop method - raise
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.stop.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            with self.assertRaises(exceptions.CommandExecutionError) as err:
                hanamod.stop('prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.stop.assert_called_once_with()
            self.assertTrue('hana error' in str(err.exception))

    def test_get_sr_state_return(self):
        '''
        Test get_sr_state method - return
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.get_sr_state.return_value = 1
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            self.assertEqual(1, hanamod.get_sr_state('prd', '00', 'pass'))
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.get_sr_state.assert_called_once_with()

    def test_get_sr_state_raise(self):
        '''
        Test get_sr_state method - raise
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.get_sr_state.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            with self.assertRaises(exceptions.CommandExecutionError) as err:
                hanamod.get_sr_state('prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.get_sr_state.assert_called_once_with()
            self.assertTrue('hana error' in str(err.exception))

    def test_sr_enable_primary_return(self):
        '''
        Test sr_enable_primary method - return
        '''
        mock_hana_inst = MagicMock()
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            hanamod.sr_enable_primary('NUE', 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.sr_enable_primary.assert_called_once_with('NUE')

    def test_sr_enable_primary_raise(self):
        '''
        Test sr_enable_primary method - raise
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.sr_enable_primary.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            with self.assertRaises(exceptions.CommandExecutionError) as err:
                hanamod.sr_enable_primary('NUE', 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.sr_enable_primary.assert_called_once_with('NUE')
            self.assertTrue('hana error' in str(err.exception))

    def test_sr_disable_primary_return(self):
        '''
        Test sr_disable_primary method - return
        '''
        mock_hana_inst = MagicMock()
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            hanamod.sr_disable_primary('prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.sr_disable_primary.assert_called_once_with()

    def test_sr_disable_primary_raise(self):
        '''
        Test sr_disable_primary method - raise
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.sr_disable_primary.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            with self.assertRaises(exceptions.CommandExecutionError) as err:
                hanamod.sr_disable_primary('prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.sr_disable_primary.assert_called_once_with()
            self.assertTrue('hana error' in str(err.exception))

    def test_sr_register_secondary_return(self):
        '''
        Test sr_register_secondary method - return
        '''
        mock_hana_inst = MagicMock()
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            hanamod.sr_register_secondary(
                'PRAGUE', 'hana01', '00', 'sync',
                'logreplay', 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.sr_register_secondary.assert_called_once_with(
                'PRAGUE', 'hana01', '00', 'sync', 'logreplay')

    def test_sr_register_secondary_raise(self):
        '''
        Test sr_register_secondary method - raise
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.sr_register_secondary.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            with self.assertRaises(exceptions.CommandExecutionError) as err:
                hanamod.sr_register_secondary(
                    'PRAGUE', 'hana01', '00', 'sync',
                    'logreplay', 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.sr_register_secondary.assert_called_once_with(
                'PRAGUE', 'hana01', '00', 'sync', 'logreplay')
            self.assertTrue('hana error' in str(err.exception))

    def test_sr_changemode_secondary_return(self):
        '''
        Test sr_changemode_secondary method - return
        '''
        mock_hana_inst = MagicMock()
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            hanamod.sr_changemode_secondary('sync', 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.sr_changemode_secondary.assert_called_once_with('sync')

    def test_sr_changemode_secondary_raise(self):
        '''
        Test sr_changemode_secondary method - raise
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.sr_changemode_secondary.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            with self.assertRaises(exceptions.CommandExecutionError) as err:
                hanamod.sr_changemode_secondary('sync', 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.sr_changemode_secondary.assert_called_once_with(
                'sync')
            self.assertTrue('hana error' in str(err.exception))

    def test_sr_unregister_secondary_return(self):
        '''
        Test sr_unregister_secondary method - return
        '''
        mock_hana_inst = MagicMock()
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            hanamod.sr_unregister_secondary('NUE', 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.sr_unregister_secondary.assert_called_once_with(
                'NUE')

    def test_sr_unregister_secondary_raise(self):
        '''
        Test sr_unregister_secondary method - raise
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.sr_unregister_secondary.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            with self.assertRaises(exceptions.CommandExecutionError) as err:
                hanamod.sr_unregister_secondary('NUE', 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.sr_unregister_secondary.assert_called_once_with(
                'NUE')
            self.assertTrue('hana error' in str(err.exception))

    def test_check_user_key_return(self):
        '''
        Test check_user_key method - return
        '''
        mock_hana_inst = MagicMock()
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            hanamod.check_user_key('key', 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.check_user_key.assert_called_once_with(
                'key')

    def test_check_user_key_raise(self):
        '''
        Test check_user_key method - raise
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.check_user_key.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            with self.assertRaises(exceptions.CommandExecutionError) as err:
                hanamod.check_user_key('key', 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.check_user_key.assert_called_once_with(
                'key')
            self.assertTrue('hana error' in str(err.exception))

    def test_create_user_key_return(self):
        '''
        Test create_user_key method - return
        '''
        mock_hana_inst = MagicMock()
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            hanamod.create_user_key(
                'key', 'env', 'user', 'pass', 'db', 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.create_user_key.assert_called_once_with(
                'key', 'env', 'user', 'pass', 'db')

    def test_create_user_key_raise(self):
        '''
        Test create_user_key method - raise
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.create_user_key.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            with self.assertRaises(exceptions.CommandExecutionError) as err:
                hanamod.create_user_key(
                    'key', 'env', 'user', 'pass', 'db', 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.create_user_key.assert_called_once_with(
                'key', 'env', 'user', 'pass', 'db')
            self.assertTrue('hana error' in str(err.exception))

    def test_create_backup_return(self):
        '''
        Test create_backup method - return
        '''
        mock_hana_inst = MagicMock()
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            hanamod.create_backup(
                'key', 'pass', 'db', 'bakcup', 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.create_backup.assert_called_once_with(
                'key', 'pass', 'db', 'bakcup')

    def test_create_backup_raise(self):
        '''
        Test create_backup method - raise
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.create_backup.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            with self.assertRaises(exceptions.CommandExecutionError) as err:
                hanamod.create_backup(
                    'key', 'pass', 'db', 'bakcup', 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.create_backup.assert_called_once_with(
                'key', 'pass', 'db', 'bakcup')
            self.assertTrue('hana error' in str(err.exception))

    def test_sr_cleanup_return(self):
        '''
        Test sr_cleanup method - return
        '''
        mock_hana_inst = MagicMock()
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            hanamod.sr_cleanup(True, 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.sr_cleanup.assert_called_once_with(True)

    def test_sr_cleanup_raise(self):
        '''
        Test sr_cleanup method - raise
        '''
        mock_hana_inst = MagicMock()
        mock_hana_inst.sr_cleanup.side_effect = hanamod.hana.HanaError(
            'hana error'
        )
        mock_hana = MagicMock(return_value=mock_hana_inst)
        with patch.object(hanamod, '_init', mock_hana):
            with self.assertRaises(exceptions.CommandExecutionError) as err:
                hanamod.sr_cleanup(False, 'prd', '00', 'pass')
            mock_hana.assert_called_once_with('prd', '00', 'pass')
            mock_hana_inst.sr_cleanup.assert_called_once_with(False)
            self.assertTrue('hana error' in str(err.exception))
