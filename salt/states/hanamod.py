# -*- coding: utf-8 -*-
'''
State module to provide SAP HANA functionality to Salt

.. versionadded:: pending

:maintainer:    Xabier Arbulu Insausti <xarbulu@suse.com>
:maturity:      alpha
:depends:       shaptools
:platform:      all

:configuration: This module requires the shaptools python module and uses the
    following defaults which may be overridden in the minion configuration:

.. code-block:: yaml

    hana.sid: 'prd'
    hana.inst: '00'
    hana.password: 'Qwerty1234'

:usage:

.. code-block:: yaml
    hana-install:
      hana.installed:
        - root_user: 'root'
        - root_password: 's'
        - software_path: '/root/sap_inst/51052481'
        - sid: 'prd'
        - inst: '00'
        - password: 'Qwerty1234'
        - config_file: salt://hana_conf/hana.conf
        - extra_parameters:
          - hostname: 'hana01'

    NUREMBERG:
      hana.sr_primary_enabled:
        - sid: 'prd'
        - inst: '00'
        - password: 'Qwerty1234'
        - cleanup: true
        - backup:
          - user: 'backupkey'
          - password:  'Qwerty1234'
          - database: 'SYSTEMDB'
          - file: 'backup'
        - userkey:
          - key: 'backupkey'
          - environment: 'hana01:30013'
          - user: 'SYSTEM'
          - password: 'Qwerty1234'
          - database: 'SYSTEMDB'
        - require:
          - hana-install
'''


# Import python libs
from __future__ import absolute_import, unicode_literals, print_function


# Import salt libs
from salt import exceptions
from salt.ext import six

__virtualname__ = 'hana'

TMP_CONFIG_FILE = '/tmp/hana.conf'


def __virtual__():  # pragma: no cover
    '''
    Only load if the hana module is in __salt__
    '''
    if 'hana.is_installed' in __salt__:
        return __virtualname__
    return False


def _parse_dict(dict_params):
    '''
    Get dictionary type variable from sls list type
    '''
    output = {}
    for item in dict_params:
        for key, value in item.items():
            output[key] = value
    return output


def installed(
        sid, inst, password,
        software_path, root_user, root_password, **kwargs):
    """
    Install SAP HANA if the platform is not installed yet. There are two ways of
    using in. The configuration file might be imported from the master to the minions
    using the *config_file* option, or if this value is not set, the sapadm_password
    and system_user_password values are mandatory

    sid
        System id of the installed hana platform
    inst
        Instance number of the installed hana platform
    password
        Password of the installed hana platform user
    software_path:
        Path where the SAP HANA software is downloaded, it must be located in
        the minion itself
    root_user
        Root user name
    root_password
        Root user password
    config_file
        If config_file paremeter is set, it will be downloaded from the master
        to the minion and used in the installation. Values in this file might
        be changed setting then in the extra_parameters dictionary using the
        exact name as in the config file as a key
    sapadm_password
        If the config file is not set, the sapadm_password is mandatory. The
        password of the sap administrator user
    system_user_password
        If the config file is not set, the system_user_password is mandatory. The
        password of the database SYSTEM (superuser) user
    extra_parameters
        Optional configuration parameters (exact name as in the config file as a key)
    """
    ret = {'name': sid,
           'changes': {},
           'result': False,
           'comment': ''}

    if __salt__['hana.is_installed'](sid, inst, password):
        ret['result'] = True
        ret['comment'] = 'HANA is already installed'
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = '{} would be installed'.format(sid)
        ret['changes']['sid'] = sid
        return ret

    try:
        #  Here starts the actual process
        if 'config_file' in kwargs:
            config_file = kwargs.get('config_file')
            __salt__['cp.get_file'](config_file, TMP_CONFIG_FILE)
            ret['changes']['config_file'] = config_file
            config_file = TMP_CONFIG_FILE
        else:
            config_file = __salt__['hana.create_conf_file'](
                software_path, TMP_CONFIG_FILE, root_user, root_password)
            config_file = __salt__['hana.update_conf_file'](
                config_file,
                sid=sid.upper(), password=password, number=inst,
                root_user=root_user,
                root_password=root_password,
                sapadm_password=kwargs.get('sapadm_password', password),
                system_user_password=kwargs.get('system_user_password'))
            ret['changes']['config_file'] = 'new'
        if 'extra_parameters' in kwargs:
            extra_parameters = _parse_dict(kwargs.get('extra_parameters'))
            config_file = __salt__['hana.update_conf_file'](
                config_file, **extra_parameters)

        __salt__['hana.install'](
            software_path, config_file, root_user, root_password)
        ret['changes']['sid'] = sid
        ret['comment'] = 'HANA installed'
        ret['result'] = True
        return ret

    except exceptions.CommandExecutionError as err:
        ret['comment'] = six.text_type(err)
        return ret
    finally:
        __salt__['file.remove'](TMP_CONFIG_FILE)
        __salt__['file.remove']('{}.xml'.format(TMP_CONFIG_FILE))


def uninstalled(sid, inst, password, root_user, root_password, **kwargs):
    '''
    Uninstall SAP HANA from node

    sid
        System id of the installed hana platform
    inst
        Instance number of the installed hana platform
    password
        Password of the installed hana platform user
    root_user
        Root user name
    root_password
        Root user password
    instalation_folder
        HANA installation folder
    '''
    ret = {'name': sid,
           'changes': {},
           'result': False,
           'comment': ''}

    if not __salt__['hana.is_installed'](sid, inst, password):
        ret['result'] = True
        ret['comment'] = 'HANA already not installed'
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = '{} would be uninstalled'.format(sid)
        ret['changes']['sid'] = sid
        return ret

    try:
        #  Here starts the actual process
        installation_folder = kwargs.get('installation_folder', None)
        __salt__['hana.uninstall'](
            root_user, root_password, sid=sid, inst=inst, password=password,
            installation_folder=installation_folder)
        ret['changes']['sid'] = sid
        ret['comment'] = 'HANA uninstalled'
        ret['result'] = True
        return ret

    except exceptions.CommandExecutionError as err:
        ret['comment'] = six.text_type(err)
        return ret


def sr_primary_enabled(name, sid, inst, password, **kwargs):
    '''
    Set the node as a primary hana node and in running state

    name
        The name of the primary node
    sid
        System id of the installed hana platform
    inst
        Instance number of the installed hana platform
    password
        Password of the installed hana platform user
    backup (optional)
        Create a new backup of the current database
        user:
            Database user
        password:
            Database user password
        database:
            Database name to backup
        file:
            Backup file name
    userkey (optional)
        Create a new key user
        key (str):
            Key name
        environment:
            Database location (host:port)
        user:
            User name
        user_password
            User password
        database (optional)
            Database name in MDC environment
    '''

    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    if not __salt__['hana.is_installed'](sid, inst, password):
        ret['comment'] = 'HANA is not installed properly with the provided data'
        return ret

    current_state = __salt__['hana.get_sr_state'](sid, inst, password)
    running = __salt__['hana.is_running'](sid, inst, password)
    #  Improve that comparison
    if running and current_state.value == 1:
        ret['result'] = True
        ret['comment'] = 'HANA node already set as primary and running'
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = '{} would be enabled as a primary node'.format(name)
        ret['changes']['primary'] = name
        ret['changes']['backup'] = kwargs.get('backup', False)
        ret['changes']['userkey'] = kwargs.get('userkey', False)
        return ret

    try:
        #  Here starts the actual process
        if not running:
            __salt__['hana.start'](sid, inst, password)
        if 'userkey' in kwargs:
            userkey_data = _parse_dict(kwargs.get('userkey'))
            __salt__['hana.create_user_key'](
                userkey_data.get('key'),
                userkey_data.get('environment'),
                userkey_data.get('user'),
                userkey_data.get('password'),
                userkey_data.get('database', None),
                sid, inst, password)
            ret['changes']['userkey'] = userkey_data.get('key')
        if 'backup' in kwargs:
            backup_data = _parse_dict(kwargs.get('backup'))
            __salt__['hana.create_backup'](
                backup_data.get('user'),
                backup_data.get('password'),
                backup_data.get('database'),
                backup_data.get('file'),
                sid, inst, password)
            ret['changes']['backup'] = backup_data.get('file')
        __salt__['hana.sr_enable_primary'](name, sid, inst, password)
        new_state = __salt__['hana.get_sr_state'](sid, inst, password)
        ret['changes']['primary'] = name
        ret['comment'] = 'HANA node set as {}'.format(new_state.name)
        ret['result'] = True
        return ret

    except exceptions.CommandExecutionError as err:
        ret['comment'] = six.text_type(err)
        return ret


def sr_secondary_registered(
        name, remote_host, remote_instance,
        replication_mode, operation_mode, sid, inst, password, **kwargs):
    '''
    Register a secondary node to an already enabled primary node

    name
        The name of the secondary node
    remote_host
        Primary node hostname
    remote_instance
        Primary node instance
    replication_mode
        Replication mode
    operation_mode
        Operation mode
    sid
        System id of the installed hana platform
    inst
        Instance number of the installed hana platform
    password
        Password of the installed hana platform user
    '''

    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    if not __salt__['hana.is_installed'](sid, inst, password):
        ret['comment'] = 'HANA is not installed properly with the provided data'
        return ret

    current_state = __salt__['hana.get_sr_state'](sid, inst, password)
    running = __salt__['hana.is_running'](sid, inst, password)
    #  Improve that comparison
    if running and current_state.value == 2:
        ret['result'] = True
        ret['comment'] = 'HANA node already set as secondary and running'
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = '{} would be registered as a secondary node'.format(name)
        ret['changes']['secondary'] = name
        return ret

    try:
        #  Here starts the actual process
        if running:
            __salt__['hana.stop'](sid, inst, password)
        __salt__['hana.sr_register_secondary'](
            name, remote_host, remote_instance,
            replication_mode, operation_mode, sid, inst, password)
        __salt__['hana.start'](sid, inst, password)
        new_state = __salt__['hana.get_sr_state'](sid, inst, password)
        ret['changes']['secondary'] = name
        ret['comment'] = 'HANA node set as {}'.format(new_state.name)
        ret['result'] = True
        return ret

    except exceptions.CommandExecutionError as err:
        ret['comment'] = six.text_type(err)
        return ret


def sr_clean(name, force, sid, inst, password):
    '''
    Clean the current node system replication mode
    name:
        Just for logging purposes
    force
        Force cleanup process
    sid
        System id of the installed hana platform
    inst
        Instance number of the installed hana platform
    password
        Password of the installed hana platform user
    '''

    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    if not __salt__['hana.is_installed'](sid, inst, password):
        ret['comment'] = 'HANA is not installed properly with the provided data'
        return ret

    current_state = __salt__['hana.get_sr_state'](sid, inst, password)
    running = __salt__['hana.is_running'](sid, inst, password)
    #  Improve that comparison
    if current_state.value == 0:
        ret['result'] = True
        ret['comment'] = 'HANA node already clean'
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['changes']['disabled'] = name
        ret['comment'] = '{} would be clean'.format(name)
        return ret

    try:
        #  Here starts the actual process
        if running:
            __salt__['hana.stop'](sid, inst, password)
        __salt__['hana.sr_cleanup'](force, sid, inst, password)
        new_state = __salt__['hana.get_sr_state'](sid, inst, password)
        ret['changes']['disabled'] = name
        ret['comment'] = 'HANA node set as {}'.format(new_state.name)
        ret['result'] = True
        return ret

    except exceptions.CommandExecutionError as err:
        ret['comment'] = six.text_type(err)
        return ret
