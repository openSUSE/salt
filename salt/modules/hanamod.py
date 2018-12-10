# -*- coding: utf-8 -*-
'''
Module to provide SAP HANA functionality to Salt

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
'''

# TODO: Add parameters description in methods docstring, using :param format

# Import Python libs
from __future__ import absolute_import, unicode_literals, print_function

from salt import exceptions

# Import third party libs
try:
    from shaptools import hana
    HAS_HANA = True
except ImportError:  # pragma: no cover
    HAS_HANA = False

__virtualname__ = 'hana'


def __virtual__():  # pragma: no cover
    '''
    Only load this module if shaptools python module is installed
    '''
    if HAS_HANA:
        return __virtualname__
    return (
        False,
        'The hana execution module failed to load: the shaptools python'
        ' library is not available.')


def _init(
        sid=None,
        inst=None,
        password=None):
    '''
    Returns an instance of the hana instance
    '''
    if sid is None:
        sid = __salt__['config.option']('hana.sid', None)
    if inst is None:
        inst = __salt__['config.option']('hana.inst', None)
    if password is None:
        password = __salt__['config.option']('hana.password', None)

    try:
        return hana.HanaInstance(sid, inst, password)
    except TypeError as err:
        raise exceptions.SaltInvocationError(str(err))


def is_installed(
        sid=None,
        inst=None,
        password=None):
    '''
    Check if SAP HANA platform is installed

    Parameters:
        sid (str): HANA system id (PRD for example)
        inst (str): HANA instance number (00 for example)
        password (str): HANA instance password

    Returns:
        bool: True if installed, False otherwise

    CLI Example:

    .. code-block:: bash

        salt '*' hana.is_installed prd '"00"' pass
    '''
    hana_inst = _init(sid, inst, password)
    return hana_inst.is_installed()


def create_conf_file(
        software_path,
        conf_file,
        root_user,
        root_password):
    '''
    Create SAP HANA configuration template file

    Parameters:
        software_path (str): Path where SAP HANA software is downloaded
        conf_file (str): Path where configuration file will be created
        root_user (str): Root user name
        root_password (str): Root user password

    Returns:
        str: Configuration file path

    CLI Example:

    .. code-block:: bash

        salt '*' hana.create_conf_file /installation_path /home/myuser/hana.conf root root
    '''
    try:
        return hana.HanaInstance.create_conf_file(
            software_path, conf_file, root_user, root_password)
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))


def update_conf_file(
        conf_file,
        extra_parameters):
    '''
    Update SAP HANA installation configuration file

    Parameters:
        conf_file (str): Path to the existing configuration file
        extra_parameters (dict): Dictionary with the values to be updated. Use the exact
            name of the SAP configuration file for the key

    Returns:
        str: Configuration file path

    CLI Example:

    .. code-block:: bash

        salt '*' hana.update_conf_file /home/myuser /home/myuser/hana.conf sid=PRD
    '''
    try:
        return hana.HanaInstance.update_conf_file(conf_file, **extra_parameters)
    except IOError as err:
        raise exceptions.CommandExecutionError(str(err))


def install(
        software_path,
        conf_file,
        root_user,
        root_password):
    '''
    Install SAP HANA with configuration file

    Parameters:
        software_path (str): Path where SAP HANA software is downloaded
        conf_file (str): Path where configuration file will be created
        root_user (str): Root user name
        root_password (str): Root user password

    CLI Example:

    .. code-block:: bash

        salt '*' hana.install /installation_path /home/myuser/hana.conf root root
    '''
    try:
        hana.HanaInstance.install(
            software_path, conf_file, root_user, root_password)
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))


def uninstall(
        root_user,
        root_password,
        installation_folder=None,
        sid=None,
        inst=None,
        password=None):
    '''
    Uninstall SAP HANA platform

    Parameters:
        root_user (str): Root user name
        root_password (str): Root user password
        installation_folder (str): Path where SAP HANA is installed (/hana/shared by default)

    CLI Example:

    .. code-block:: bash

        salt '*' hana.uninstall root root
    '''
    hana_inst = _init(sid, inst, password)
    kwargs = {}
    if installation_folder:
        kwargs['installation_folder'] = installation_folder
    try:
        hana_inst.uninstall(root_user, root_password, **kwargs)
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))


def is_running(
        sid=None,
        inst=None,
        password=None):
    '''
    Check if SAP HANA daemon is running

    Returns:
        bool: True if running, False otherwise

    CLI Example:

    .. code-block:: bash

        salt '*' hana.is_running prd '"00"' pass
    '''
    hana_inst = _init(sid, inst, password)
    return hana_inst.is_running()


# pylint:disable=W1401
def get_version(
        sid=None,
        inst=None,
        password=None):
    '''
    Get SAP HANA version

    CLI Example:

    .. code-block:: bash

        salt '*' hana.get_version prd '"00"' pass
    '''
    hana_inst = _init(sid, inst, password)
    try:
        return hana_inst.get_version()
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))


def start(
        sid=None,
        inst=None,
        password=None):
    '''
    Start hana instance

    CLI Example:

    .. code-block:: bash

        salt '*' hana.start prd '"00"' pass
    '''
    hana_inst = _init(sid, inst, password)
    try:
        hana_inst.start()
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))


def stop(
        sid=None,
        inst=None,
        password=None):
    '''
    Stop hana instance

    CLI Example:

    .. code-block:: bash

        salt '*' hana.stop prd '"00"' pass
    '''
    hana_inst = _init(sid, inst, password)
    try:
        hana_inst.stop()
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))


def get_sr_state(
        sid=None,
        inst=None,
        password=None):
    '''
    Get system replication status in th current node

    Returns:
        SrStates: System replication state

    CLI Example:

    .. code-block:: bash

        salt '*' hana.get_sr_state prd '"00"' pass
    '''
    hana_inst = _init(sid, inst, password)
    try:
        return hana_inst.get_sr_state()
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))


def sr_enable_primary(
        name,
        sid=None,
        inst=None,
        password=None):
    '''
    Enable SAP HANA system replication as primary node

    Parameters:
        name (str): Name to give to the node

    CLI Example:

    .. code-block:: bash

        salt '*' hana.sr_enable_primary NUREMBERG prd '"00"' pass
    '''
    hana_inst = _init(sid, inst, password)
    try:
        hana_inst.sr_enable_primary(name)
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))


def sr_disable_primary(
        sid=None,
        inst=None,
        password=None):
    '''
    Disable SAP HANA system replication as primary node

    CLI Example:

    .. code-block:: bash

        salt '*' hana.sr_disable_primary prd '"00"' pass
    '''
    hana_inst = _init(sid, inst, password)
    try:
        hana_inst.sr_disable_primary()
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))


def sr_register_secondary(
        name,
        remote_host,
        remote_instance,
        replication_mode,
        operation_mode,
        sid=None,
        inst=None,
        password=None):
    '''
    Register SAP HANA system replication as secondary node

    Parameters:
        name (str): Name to give to the node
        remote_host (str): Primary node hostname
        remote_instance (str): Primary node instance
        replication_mode (str): Replication mode
        operation_mode (str): Operation mode

    CLI Example:

    .. code-block:: bash

        salt '*' hana.sr_register_secondary PRAGUE hana01 00 sync logreplay prd '"00"' pass
    '''
    hana_inst = _init(sid, inst, password)
    try:
        hana_inst.sr_register_secondary(
            name, remote_host, remote_instance,
            replication_mode, operation_mode)
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))


def sr_changemode_secondary(
        new_mode,
        sid=None,
        inst=None,
        password=None):
    '''
    Change secondary synchronization mode

    Parameters:
        new_mode (str): New mode between sync|syncmem|async

    CLI Example:

    .. code-block:: bash

        salt '*' hana.sr_changemode_secondary sync prd '"00"' pass
    '''
    hana_inst = _init(sid, inst, password)
    try:
        hana_inst.sr_changemode_secondary(new_mode)
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))


def sr_unregister_secondary(
        primary_name,
        sid=None,
        inst=None,
        password=None):
    '''
    Unegister SAP HANA system replication from primary node

    Parameters:
        name (str): Name to give to the node

    CLI Example:

    .. code-block:: bash

        salt '*' hana.sr_unregister_secondary NUREMBERG prd '"00"' pass
    '''
    hana_inst = _init(sid, inst, password)
    try:
        hana_inst.sr_unregister_secondary(primary_name)
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))


def check_user_key(
        key,
        sid=None,
        inst=None,
        password=None):
    '''
    Check the use key existance

    Parameters:
        key (str): User key name

    Returns:
        bool: True if it exists, False otherwise

    CLI Example:

    .. code-block:: bash

        salt '*' hana.check_user_key key prd '"00"' pass
    '''
    hana_inst = _init(sid, inst, password)
    try:
        return hana_inst.check_user_key(key)
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))


def create_user_key(
        key,
        environment,
        user,
        user_password,
        database=None,
        sid=None,
        inst=None,
        password=None):
    '''
    Create user key entry for the database

    Parameters:
        key (str): User key
        environment (str): Key environment
        user (srt): User name
        user_password (str): User password
        database (str, opt): Database name

    CLI Example:

    .. code-block:: bash

        salt '*' hana.create_user_key key hana01:30013 SYSTEM pass SYSTEMDB prd '"00"' pass
    '''
    hana_inst = _init(sid, inst, password)
    try:
        hana_inst.create_user_key(
            key, environment, user, user_password, database)
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))


def create_backup(
        user_key,
        user_password,
        database,
        backup_name,
        sid=None,
        inst=None,
        password=None):
    '''
    Create the primary node backup

    Parameters:
        user_key (str): User key name
        user_password (str): User key password
        database (str): Database name
        back_name (str): Backup name

    CLI Example:

    .. code-block:: bash

        salt '*' hana.create_backup key pass SYSTEMDB backup prd '"00"' pass
    '''
    hana_inst = _init(sid, inst, password)
    try:
        hana_inst.create_backup(
            user_key, user_password, database, backup_name)
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))


def sr_cleanup(
        force=False,
        sid=None,
        inst=None,
        password=None):
    '''
    Clean system replication state

    Parameters:
        force (bool): Force cleanup

    CLI Example:

    .. code-block:: bash

        salt '*' hana.sr_cleanup true prd '"00"' pass
    '''
    hana_inst = _init(sid, inst, password)
    try:
        hana_inst.sr_cleanup(force)
    except hana.HanaError as err:
        raise exceptions.CommandExecutionError(str(err))
