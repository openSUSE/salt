# Import Python Libs
from __future__ import absolute_import, print_function, unicode_literals
import os
import json
import gzip
import re
import time
import logging
import xml.etree.ElementTree as ET
import hashlib
import pathlib
import requests
import salt.utils.platform


# Module to get the details of the system
log = logging.getLogger(__name__)
__virtualname__ = "redfish"
__proxyenabled__ = ["redfish"]


def __virtual__():
    """
    Only work on proxy
    """
    if salt.utils.platform.is_proxy():
        return __virtualname__
    return (False, "The redfish module failed to load only available on proxy minions.")


# Module to get the boot devices present in the system
def system_get_current_boot_devices():
    """
    This module is used to get the details of the boot options
    present in the current system

    Return: list of allowable boot values supported by the system

    CLI example:
    .. code-block:: bash
                salt '*' redfish.system_get_current_boot_devices
    """
    boot_device = __proxy__["redfish.http_get"](
        "/redfish/v1/Systems/System.Embedded.1/"
    )
    # boot_device = __proxy__["redfish.http_get"]("/redfish/v1/Systems/System.Embedded.1/")
    if "Boot" in boot_device:
        return boot_device["Boot"]["BootSourceOverrideTarget@Redfish.AllowableValues"]
    return boot_device


# Module to identify reset types provided by the system
def system_get_reset_type():
    """
    This module is used to provide different reset options
    present in the current system

    Return: allowable reset types supported by the system

    CLI example:
    .. code-block:: bash
                salt '*' redfish.system_get_reset_type
    """
    reset_type = __proxy__["redfish.http_get"]("/redfish/v1/Systems/System.Embedded.1/")
    if "Actions" in reset_type:
        return reset_type["Actions"]["#ComputerSystem.Reset"][
            "ResetType@Redfish.AllowableValues"
        ]
    return reset_type


# Module to display boot details
def system_get_boot_options():
    """
    This module is used to get the detailed information of the
    supported boot options in the system

    Return: dictionary with the detailed information of boot devices

    CLI example:
    .. code-block:: bash
                salt '*' redfish.system_get_boot_options
    """
    options = {}
    boot_options = __proxy__["redfish.http_get"](
        "/redfish/v1/Systems/System.Embedded.1/BootOptions"
    )
    if "Members" in boot_options:
        for i in boot_options["Members"]:
            logging.debug(i)
            boot_option_key = os.path.basename(i["@odata.id"])
            boot_option_value = __proxy__["redfish.http_get"](i["@odata.id"])
            logging.debug(boot_option_value)
            if boot_option_value:
                options[boot_option_key] = boot_option_value
            else:
                return boot_option_value
        return options

    return boot_options


# Module to get the system power info
def system_get_psu_info():
    """
    This module is used to get the details of the power source information
    of the present system.

    Return: Dictionary with the sources of power as key and
            detailed information as the value

    CLI example:
    .. code-block:: bash
                salt '*' redfish.system_get_psu_info
    """
    psu = {}
    sys_info = __proxy__["redfish.http_get"]("/redfish/v1/Systems/System.Embedded.1/")
    if "Links" in sys_info:
        for i in sys_info["Links"]["PoweredBy"]:
            psu_key = os.path.basename(i["@odata.id"])
            psu_value = __proxy__["redfish.http_get"](i["@odata.id"])
            if psu_value:
                psu[psu_key] = psu_value
            else:
                return psu_value
        return psu
    return sys_info


# Module to get thermal details of chassis
def system_get_chassis_cooling_devices():
    """
    This module is used to get the information of the processor fans used
    to cool the chassis of the system

    Return: Dictionary with the cooling device as key and
            its information as the value

    CLI example:
    .. code-block:: bash
                salt '*' redfish.system_get_chassis_cooling_devices
    """

    cooling_devices = {}
    sys_info = __proxy__["redfish.http_get"]("/redfish/v1/Systems/System.Embedded.1/")
    if "Links" in sys_info:
        for i in sys_info["Links"]["CooledBy"]:
            cooling_device_key = os.path.basename(i["@odata.id"])
            cooling_device_value = __proxy__["redfish.http_get"](i["@odata.id"])
            if cooling_device_value:
                cooling_devices[cooling_device_key] = cooling_device_value
            else:
                return cooling_device_value
        return cooling_devices
    return sys_info


# Module to get the details of CPUs of the system
def system_get_processor_info():
    """
    This module is used to get the details of the processors present
    in the system

    Return: Dictionary with processor(CPU) name as key and
            its information as value

    CLI example:
    .. code-block:: bash
                salt '*' redfish.system_get_processor_info
    """
    processors = {}
    proc = __proxy__["redfish.http_get"](
        "/redfish/v1/Systems/System.Embedded.1/Processors"
    )
    if "Members" in proc:
        for i in proc["Members"]:
            processor_key = os.path.basename(i["@odata.id"])
            processor_value = __proxy__["redfish.http_get"](i["@odata.id"])
            processors[processor_key] = processor_value
        return processors
    return proc


# Module to get secure boot information
def system_get_secureboot_info():
    """
    This module is used to provide the secure boot details of the system

    Return: Information of the secure booting in the system

    CLI example:
    .. code-block:: bash
                salt '*' redfish.system_get_secureboot_info
    """
    secure_boot = __proxy__["redfish.http_get"](
        "/redfish/v1/Systems/System.Embedded.1/SecureBoot"
    )
    return secure_boot


# Module to get the storage controllers in the system
def system_get_storage_controllers_info():
    """
    This module is used to get the storage devices present in the system

    Return: Dictionary with storage controller name as key and
            disks information of the controller as values.

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_get_storage_controllers_info
    """
    ctrl_info = {}
    ctrls = __proxy__["redfish.http_get"](
        "/redfish/v1/Systems/System.Embedded.1/Storage"
    )
    if "Members" in ctrls:
        for i in ctrls["Members"]:
            ctrl_key = os.path.basename(i["@odata.id"])
            ctrl_value = __proxy__["redfish.http_get"](i["@odata.id"])
            ctrl_info[ctrl_key] = ctrl_value
        return ctrl_info
    return ctrls


# Module to get the disks info in the system
def system_get_disk_drive_info():
    """
    This module is used to get the information of the each disk of
    different storage controllers present in the system

    Return: Dictionary with each disk name as key and
            disk information as value

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_get_disk_drive_info
    """

    disk_info = {}
    ctrls = __proxy__["redfish.http_get"](
        "/redfish/v1/Systems/System.Embedded.1/Storage"
    )
    if ctrls:
        for i in ctrls["Members"]:
            ctrl_key = os.path.basename(i["@odata.id"])
            ctrl_value = __proxy__["redfish.http_get"](i["@odata.id"])
            disk_info[ctrl_key] = {}
            for j in ctrl_value["Drives"]:
                disk_key = os.path.basename(j["@odata.id"])
                disk_value = __proxy__["redfish.http_get"](j["@odata.id"])
                disk_info[ctrl_key][disk_key] = disk_value
        return disk_info
    return ctrls


# Module to get the virtual disks info in the system
def system_get_virtual_disk_info():
    """
    This module is used to get the information of the virtual disks of
    different storage controllers if present in the system

    Return: Dictionary with each virtual disk name as key and
            disk information as value

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_get_virtual_disk_info
    """
    vds_info = {}
    ctrls = __proxy__["redfish.http_get"](
        "/redfish/v1/Systems/System.Embedded.1/Storage"
    )
    if ctrls:
        for i in ctrls["Members"]:
            ctrl_key = os.path.basename(i["@odata.id"])
            vds_info[ctrl_key] = {}
            volumes = __proxy__["redfish.http_get"](
                "/redfish/v1/Systems/System.Embedded.1/Storage/{ctrl_key}/Volumes".format(
                    ctrl_key=ctrl_key
                )
            )
            for j in volumes["Members"]:
                vd_key = os.path.basename(j["@odata.id"])
                vd_value = __proxy__["redfish.http_get"](j["@odata.id"])
                vds_info[ctrl_key][vd_key] = vd_value
        return vds_info
    return ctrls


def get_lc_logs():
    """
    This module is used to get life cycle controler logs.

    Return: Dictionary with life cycle controller logs

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.get_lc_logs
    """
    return __proxy__["redfish.http_get"](
        "/redfish/v1/Managers/iDRAC.Embedded.1/Logs/Lclog"
    )


def get_sel_logs():
    """
    This module is used to get System Event Log (SEL).

    Return: Dictionary with life cycle controller logs

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.get_sel_logs
    """
    return __proxy__["redfish.http_get"](
        "/redfish/v1/Managers/iDRAC.Embedded.1/Logs/Sel"
    )


def get_fault_logs():
    """
    This module is used to get fault logs.

    Return: Dictionary with life cycle controller logs

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.get_fault_logs
    """
    return __proxy__["redfish.http_get"](
        "/redfish/v1/Managers/iDRAC.Embedded.1/Logs/FaultList"
    )


# Module to get details of the removable disks
def manager_get_virtual_media_removable_disk():
    """
    This module is used to provide the removable disk details

    Return: Description of the removable disks present in the system

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.manager_get_virtual_media_removable_disk
    """

    return __proxy__["redfish.http_get"](
        "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/RemovableDisk"
    )


# Module to get details of cd/dvd
def manager_get_virtual_media_cd():
    """
    This module is used to provide the cd/dvd details

    Return: Description of the cd/dvd present in the system

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.manager_get_virtual_media_cd
    """

    return __proxy__["redfish.http_get"](
        "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/CD"
    )


# Module to get network adapters
def system_get_network_adapters():
    """
    This module is used to extract the details of network adapters

    Return: Dictionary with each adapter name as key and
            their functions as value

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_get_network_adapters
    """
    adapters = {}
    ret = __proxy__["redfish.http_get"](
        "/redfish/v1/Systems/System.Embedded.1/NetworkAdapters"
    )
    if "Members" in ret:
        for i in ret["Members"]:
            adapter_key = os.path.basename(i["@odata.id"])
            adapter_value = __proxy__["redfish.http_get"](i["@odata.id"])
            logging.debug(adapter_value)
            adapters[adapter_key] = adapter_value
        return adapters
    return ret


# Module to get details of network adapter functions
def system_get_network_adapter_device_functions(adapter):
    """
    This module is used to extract the details of the functions provided
    by the specified network adapter

    Param:
        - adapter: name of the adapter whose functions are required

    Return: Dictionary with each function name as key and
            description of the function as value

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_get_network_adapter_device_functions
    """

    funs = {}
    ret = __proxy__["redfish.http_get"](
        "/redfish/v1/Systems/System.Embedded.1/NetworkAdapters/{adapter}/NetworkDeviceFunctions".format(
            adapter=adapter
        )
    )
    if "Members" in ret:
        for i in ret["Members"]:
            fun_key = os.path.basename(i["@odata.id"])
            fun_value = __proxy__["redfish.http_get"](i["@odata.id"])
            funs[fun_key] = fun_value
        return funs
    return ret


# Module to get ethernet devices in the system
def system_get_ethernet_devices():
    """
    This module is used to extract the details of the network interfaces
    present in the system

    Return: Dictionary with each ethernet device name as key and
            their description as value

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_get_ethernet_devices
    """
    ethers = {}
    ret = __proxy__["redfish.http_get"](
        "/redfish/v1/Systems/System.Embedded.1/EthernetInterfaces"
    )
    if "Members" in ret:
        for i in ret["Members"]:
            ether_key = os.path.basename(i["@odata.id"])
            ether_value = __proxy__["redfish.http_get"](i["@odata.id"])
            ethers[ether_key] = ether_value
        return ethers
    return ret


# Module to reset the bios to default
def system_bios_reset_to_default():
    """
    This module is used to reset the bios to default settings in the system

    Return: details of the post command after resetting the bios

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_bios_reset_to_default
    """
    reset_to_default = __proxy__["redfish.http_post"](
        uri="/redfish/v1/Systems/System.Embedded.1/Bios/Actions/Bios.ResetBios",
        headers={"content-type": "application/json"},
        payload={},
    )
    if reset_to_default:
        restart = system_reset(reset_type="ForceRestart")
        if restart:
            time.sleep(300)
            return {"result": True, "message": "BIOS reset to default successfully"}

    return  {"result": False, "message": "BIOS reset to default failed"}


# Module to reset the system
def system_reset(reset_type):
    """
    This module is used to reset the system based on the reset type specified

    Param:
        - reset_type: type of reset required by user and supported by system

    Return: Description of the post command after execution

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_reset reset_type=ForceOff
    """
    reset_values = [
        "On",
        "ForceOff",
        "ForceRestart",
        "GracefulShutdown",
        "PushPowerButton",
        "Nmi",
    ]
    if reset_type in reset_values:
        payload = {}
        headers = {}
        uri = "/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset"
        payload["ResetType"] = reset_type
        headers["content-type"] = "application/json"
        ret = __proxy__["redfish.http_post"](uri, headers=headers, payload=payload)
        return ret
    logging.error("reset_type in not valid")
    return False


# Module to attach image url to CD
def manager_attach_cd(image_url, force=False):
    """
    This module is used to attach the image url of the required OS by the user
    by means of CD

    Param:
        - image_url: url location of the required OS
        - force: boolean value, if it is true check if any image is already exists
                 and remove it and insert new image url else directly attach it

    Return: Description of the post command after execution

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.manager_attach_cd image_url=http://100.98.4.4/suse/SLES-15-SP1.iso force=true
    """

    if force:
        cd_status = manager_get_virtual_media_cd()
        if "Inserted" in cd_status:
            if cd_status["Inserted"]:
                cd_eject = manager_eject_cd()
                time.sleep(5)
                if not cd_eject:
                    return cd_eject
    uri = "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/CD/Actions/VirtualMedia.InsertMedia"
    payload = {
        "Image": "{image_url}".format(image_url=image_url),
        "Inserted": True,
        "WriteProtected": True,
    }
    headers = {"content-type": "application/json"}
    ret = __proxy__["redfish.http_post"](uri=uri, headers=headers, payload=payload)
    if ret:
        ret["changes"] = "Attached {image_url} ".format(image_url=image_url)
    return ret


# Module to attach image url to removable disk
def manager_attach_removable_disk(image_url, force=False):
    """
    This module is used to attach the image url of the required OS by the user
    by means of removable disk

    Param:
        - image_url: url location of the required OS

    Return: Description of the post command after execution

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.manager_attach_cd  image_url=http://100.98.4.4/suse/OEMDRV.img force=true
    """
    if force:
        cd_status = manager_get_virtual_media_removable_disk()
        if "Inserted" in cd_status:
            if cd_status["Inserted"]:
                cd_eject = manager_eject_removable_disk()
                time.sleep(5)
                if not cd_eject:
                    return cd_eject

    uri = "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/RemovableDisk/Actions/VirtualMedia.InsertMedia"
    payload = {"Image": image_url, "Inserted": True, "WriteProtected": True}
    headers = {"content-type": "application/json"}
    ret = __proxy__["redfish.http_post"](uri=uri, headers=headers, payload=payload)
    if ret:
        ret["changes"] = "Attached {image_url} ".format(image_url=image_url)
    return ret


# Module to eject the CD
def manager_eject_cd():
    """
    This module is used to eject the media attached through CD

    Return: Description of the post command after execution

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.manager_eject_cd
    """
    cd_status = manager_get_virtual_media_cd()
    if "Inserted" in cd_status:
        if not cd_status["Inserted"]:
            return True
        uri = "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/CD/Actions/VirtualMedia.EjectMedia"
        payload = {}
        headers = {"content-type": "application/json"}
        ret = __proxy__["redfish.http_post"](uri=uri, headers=headers, payload=payload)
        if ret:
            return True
        return False
    return False


# Module to eject the removable disk
def manager_eject_removable_disk():
    """
    This module is used to eject the media attached through removable disk

    Return: Description of the post command after execution

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.manager_eject_removable_disk
    """

    uri = "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/RemovableDisk/Actions/VirtualMedia.EjectMedia"
    payload = {}
    headers = {"content-type": "application/json"}
    ret = __proxy__["redfish.http_post"](uri=uri, headers=headers, payload=payload)
    if ret:
        ret["changes"] = "Ejected Removable Disk "
    return ret


# Module to get the firmware of the system
def get_firmware_inventory(fw_type=None):
    """
    This module is used to extract the details of the firmware in the system

    Param:
        - fw_type: To specify which type of firmware is requied whether
                previous, current or installed. If None, all are returned.

    Return: Dictionary with the required type of firmware specified by user

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.get_firmware_inventory  type=installed
    """

    inventory = {}
    inv_type = {}
    ret = __proxy__["redfish.http_get"]("/redfish/v1/UpdateService/FirmwareInventory")
    if "Members" in ret:
        for i in ret["Members"]:
            fw_key = os.path.basename(i["@odata.id"])
            fw_value = __proxy__["redfish.http_get"](i["@odata.id"])
            inventory[fw_key] = fw_value
        if fw_type is None:
            return inventory
        for i in inventory.keys():
            if fw_type in i:
                inv_type[i] = inventory[i]
        return inv_type
    return ret


# Module to set the one time boot device
def system_onetime_boot(boot_mode, boot_device):
    """
    This module is used to set the one time boot device of the system for next boot

    Param:
        - name: Name of the module
        - boot_mode: to define either bios or uefi mode
        - boot_device: to define the device from where to boot

    Return: Description of the post command after exeution

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_Onetime_Boot name="Onetimeboot"
                             boot_mode="Uefi" boot_device="Pxe"
    """

    uri = "/redfish/v1/Systems/System.Embedded.1"
    headers = {"content-type": "application/json"}

    if boot_mode == "Bios":
        payload = {"Boot": {"BootSourceOverrideTarget": boot_device}}
    elif boot_mode == "Uefi":
        payload = {
            "Boot": {
                "BootSourceOverrideTarget": "UefiTarget",
                "UefiTargetBootSourceOverride": boot_device,
            }
        }
    ret = __proxy__["redfish.http_patch"](uri, headers, payload)
    if ret:
        return True
    return False


def system_onetime_boot_device_uefi(boot_device):
    """
    This module is used to set the one time boot device of the system for next boot

    Param:
        - name: Name of the module
        - boot_mode: to define either bios or uefi mode
        - boot_device: to define the device from where to boot

    Return: Description of the post command after exeution

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_Onetime_Boot name="Onetimeboot"
                             boot_mode="Uefi" boot_device="Pxe"
    """

    uri = "/redfish/v1/Systems/System.Embedded.1"
    headers = {"content-type": "application/json"}
    payload = {
        "Boot": {
            "BootSourceOverrideTarget": "UefiTarget",
            "UefiTargetBootSourceOverride": boot_device,
        }
    }
    ret = __proxy__["redfish.http_patch"](uri, headers, payload)
    if ret:
        return True
    return False


# Module to get the bios attributes
def system_get_bios_attributes():
    """
    This is used to get the attributes of BIOS required by the user

    :param:
        - attribute_names: list of attibutes required by the user
                            if all attributes are required pass attribute_names="all"

    CLI Example:
    .. code-block:: bash
        salt '*' redfish.system_get_bios_attributes attribute_names="all"
    """
    return __proxy__["redfish.http_get"]("/redfish/v1/Systems/System.Embedded.1/Bios")


# Module to get the system info
def get_system_info():
    """
    This module is used to extract the current system information

    Return: Description of the system

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.get_system_info
    """
    return __proxy__["redfish.http_get"]("/redfish/v1/Systems/System.Embedded.1")


# Module to get the boot order of the system
def system_get_boot_order():
    """
    This module is used to get the booting order of the system

    Return: Boot order of the system

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_get_boot_order
    """
    boot = __proxy__["redfish.http_get"]("/redfish/v1/Systems/System.Embedded.1")
    if "Boot" in boot:
        return boot["Boot"]["BootOrder"]
    return boot


# Module to set the first boot device
def system_set_first_boot_device(device):
    """
    This module is to set the boot order and make the device specified by the
    user in first position

    Param:
        - device: name of the device that is to be booted from for the first time

    Return: Description of the patch command after execution

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_set_first_boot_device device="Pxe"
    """

    first_device = None
    sysinfo = __proxy__["redfish.http_get"]("/redfish/v1/Systems/System.Embedded.1/")
    boot_list = sysinfo["Boot"]["BootOrder"]
    boot_option = system_get_boot_options()
    if boot_option:
        for option in boot_option:
            if device.lower() in boot_option[option]["DisplayName"].lower():
                first_device = os.path.basename(boot_option[option]["@odata.id"])
                break
    boot_list = [first_device] + boot_list
    payload = {"Boot": {"BootOrder": boot_list}}
    headers = {"content-type": "application/json"}
    return __proxy__["redfish.http_patch"](
        uri="/redfish/v1/Systems/System.Embedded.1/", headers=headers, payload=payload
    )


# module to provide chassis information
def get_chassis_info():
    """
    This module is provided chassis information


    Return: dictionary of chassis information

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.get_chassis_info
    """
    return __proxy__["redfish.http_get"]("/redfish/v1/Chassis/System.Embedded.1")


def chassis_reset(reset_type):
    """
    This module is to reset chassis

    Param:
        - device: type of chasis reset

    Return: Description of the patch command after execution

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.chassis_reset reset_type="ForceOff"
    """
    if reset_type in ["On", "ForceOff"]:
        payload = {}
        headers = {}
        uri = "/redfish/v1/Chassis/System.Embedded.1/Actions/Chassis.Reset"
        payload["ResetType"] = reset_type
        headers["content-type"] = "application/json"
        ret = __proxy__["redfish.http_post"](uri, headers=headers, payload=payload)
        return ret
    logging.error("reset_type in not valid")
    return False


def chassis_get_assembly_info():
    """
    This module is to get chasis parts information

    Return: list of chasis part detail

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.chassis_get_assembly_info
    """
    return __proxy__["redfish.http_get"](
        "/redfish/v1/Chassis/System.Embedded.1/Assembly"
    )


def chassis_get_cooled_by_info():
    """
    This module is to get chasis cooled by devices

    Return: list of chassis cooling devices

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.chassis_get_cooled_by_info
    """
    chassis_info = __proxy__["redfish.http_get"](
        "/redfish/v1/Chassis/System.Embedded.1/"
    )
    if "Links" in chassis_info:
        return chassis_info["Links"]["CooledBy"]
    logging.error("failed to get info from system")
    return chassis_info


def chassis_get_powered_by_info():
    """
    This module is to get chasis powered  devices

    Return: list of chassis power supply devices

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.chassis_get_powered_by_info
    """
    chassis_info = __proxy__["redfish.http_get"](
        "/redfish/v1/Chassis/System.Embedded.1/"
    )
    if "Links" in chassis_info:
        return chassis_info["Links"]["PoweredBy"]
    logging.error("failed to get info from system")
    return chassis_info


def chassis_get_power_control_info():
    """
    This module provide detailed information about power control of chassis

    Return: chassis power control information

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.chassis_get_power_control_info
    """
    power_control = __proxy__["redfish.http_get"](
        "/redfish/v1/Chassis/System.Embedded.1/Power"
    )
    if "PowerControl" in power_control:
        return power_control["PowerControl"]
    return power_control


def chassis_get_power_consumed_watts():
    """
    This module provide detailed information about power consumed by  system in watts

    Return: chassis power consumed in watts

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.chassis_get_power_consumed_watts
    """

    power_control = __proxy__["redfish.http_get"](
        "/redfish/v1/Chassis/System.Embedded.1/Power"
    )
    if "PowerControl" in power_control:
        return power_control["PowerControl"][0]["PowerConsumedWatts"]
    return power_control


def update_service_get_fw_components(comp_type=None):
    """
    This module provide firmware components
    Param:
        - comp_type: type of firmware component EX for BIOS component id is 159

    Return: chassis power consumed in watts

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.chassis_get_power_consumed_watts comp_type=159
    """
    components = []
    firmware_inv = __proxy__["redfish.http_get"](
        "/redfish/v1/UpdateService/FirmwareInventory"
    )
    if firmware_inv["Members"]:
        for i in firmware_inv["Members"]:
            if comp_type:
                if comp_type in os.path.basename(i["@odata.id"]):
                    components.append(os.path.basename(i["@odata.id"]).split("-")[1])
            else:
                components.append(os.path.basename(i["@odata.id"]).split("-")[1])
        return components
    return firmware_inv


# Module to download and parse the catalogue file
def parse_catalogue_file(system, components):
    """
    This is used to get the details of the specified dell poweredge server components.
    We can get the catalogue file from downloads.dell.com where whole dell components
    information is available.

    Params:
        - system : specify which poweredge server
        - components : a list of components whose information is required

    Return: Dictionary with component_id as key and
            result as value

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.parse_catalogue_file system="R730"
                                                    components=[159,25227]
    """
    url = "http://downloads.dell.com/catalog/Catalog.gz"
    filename = url.split("/")[-1]
    with open(filename, "wb") as file_d:
        req = requests.get(url)
        file_d.write(req.content)
        file_d.close()

    data = gzip.open(filename, "r")
    tree = ET.parse(data)

    comp = {}
    for soft_comp in tree.findall("SoftwareComponent"):
        for supp_device in soft_comp.findall("SupportedDevices"):
            for device in supp_device.findall("Device"):
                for i in range(len(components)):
                    if supp_device.get("componentID") == str(components[i]):
                        for supp_sys in soft_comp.findall("SupportedSystems"):
                            for brand in supp_sys.findall("Brand"):
                                for model in brand.findall("Model"):
                                    for display in model.findall("Display"):
                                        if (
                                            display.text == system
                                            and os.path.basename(
                                                soft_comp.get("path")
                                            ).split(".")[-1]
                                            == "EXE"
                                        ):
                                            comp[str(components[i])] = {
                                                "path": soft_comp.get("path"),
                                                "version": soft_comp.get(
                                                    "vendorVersion"
                                                ),
                                                "result": True,
                                                "rebootRequired": soft_comp.get(
                                                    "rebootRequired"
                                                ),
                                                "hashMD5": soft_comp.get("hashMD5"),
                                            }

    for i in range(len(components)):
        if str(components[i]) not in comp.keys():
            comp[str(components[i])] = {
                "path": "Not found",
                "version": "Not found",
                "result": False,
                "rebootRequired": "None",
                "hashMD5": "None",
            }

    return comp


# Module to know the current version of the specified components
def get_current_version(component_ids):
    """
    This is used to return the details of the current version of the specified components required by the user.
    If the specified componet is found results will be displayed else it will be displayed as not found.

    Params:
        - component_ids: It is a list to provide the IDs of required components

    Return: Dictionary with component_id as key and
            result as value

    CLI Example:
    .. code-block:: bash
                salt-call '*' redfish.get_current_version component_ids=[159,101277,252752]
    """
    fws = {}
    inventory = __proxy__["redfish.http_get"](
        "/redfish/v1/UpdateService/FirmwareInventory"
    )
    if inventory:
        for comp_id in component_ids:
            for i in inventory["Members"]:
                inv_detail = __proxy__["redfish.http_get"](i["@odata.id"])
                # logging.debug(inv_detail)
                if inv_detail:
                    if str(comp_id) == str(inv_detail["SoftwareId"]):
                        fws[comp_id] = {
                            "name": inv_detail["Name"],
                            "version": inv_detail["Version"],
                        }
                    else:
                        continue
                return inv_detail
        return fws
    return inventory


# Module to know the previous version of the specified components
def get_previous_version(component_ids):
    """
    This is used to return the details of the previous version of the specified components required by the user.
    If the specified componet is found results will be displayed else it will be displayed as not found.

    Params:
        - component_ids: It is a list to provide the IDs of required components

    Return: Dictionary with component_id as key and
            result as value

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.get_previous_version component_ids=[159,101277,252752]
    """
    fws = {}
    inv = __proxy__["redfish.http_get"]("/redfish/v1/UpdateService/FirmwareInventory")
    if inv:
        for comp_id in component_ids:
            for i in inv["Members"]:
                if "Previous" in os.path.basename(i["@odata.id"]):
                    inv_detail = __proxy__["redfish.http_get"](i["@odata.id"])
                    if inv_detail:
                        if str(comp_id) == str(inv_detail["SoftwareId"]):
                            fws[comp_id] = {
                                "name": inv_detail["Name"],
                                "version": inv_detail["Version"],
                            }
                        else:
                            continue
                    else:
                        return inv_detail
                else:
                    continue
        return fws
    return inv


def get_avaiable_fw_versions(component_ids):
    """
    This is used to return the details of the avaiable version of the specified components required by the user.
    If the specified componet is found results will be displayed else it will be displayed as not found.

    Params:
        - component_ids: It is a list to provide the IDs of required components

    Return: Dictionary with component_id as key and
            result as value

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.get_avaiable_fw_versions component_ids=[159,101277,252752]
    """

    fws = {}
    inv = __proxy__["redfish.http_get"]("/redfish/v1/UpdateService/FirmwareInventory")
    if inv:
        for comp_id in component_ids:
            for i in inv["Members"]:
                if "Available" in os.path.basename(i["@odata.id"]):
                    inv_detail = __proxy__["redfish.http_get"](i["@odata.id"])
                    if inv_detail:
                        if str(comp_id) == str(inv_detail["SoftwareId"]):
                            fws[comp_id] = {
                                "name": inv_detail["Name"],
                                "version": inv_detail["Version"],
                                "uri": inv_detail["@odata.id"],
                            }
                        else:
                            continue
                    else:
                        return inv_detail
                else:
                    continue
        return fws
    return inv


# Module to know the installed version of the specified component
def get_installed_version(component_ids):
    """
    This is used to return the details of the installed version of the specified components required by the user.
    If the specified componet is found results will be displayed else it will be displayed as not found.

    Params:
        - component_ids: It is a list to provide the IDs of required components

    Return: Dictionary with component_id as key and
            result as value

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.get_installed_version component_ids=[159,101277,252752]
    """
    fws = {}
    inv = __proxy__["redfish.http_get"]("/redfish/v1/UpdateService/FirmwareInventory")
    if inv:
        for comp_id in component_ids:
            for i in inv["Members"]:
                if "Installed" in os.path.basename(i["@odata.id"]):
                    inv_detail = __proxy__["redfish.http_get"](i["@odata.id"])
                    if inv_detail:
                        if str(comp_id) == str(inv_detail["SoftwareId"]):
                            fws[comp_id] = {
                                "name": inv_detail["Name"],
                                "version": inv_detail["Version"],
                            }
                        else:
                            continue
                    else:
                        return inv_detail
                else:
                    continue
        return fws
    return inv


def delete_fw_payload(uri):
    """
    This is used to delete firmware payload

    Params:
        - uri: firmware payload uri

    Return: Dictionary with status

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.delete_fw_payload  uri=/redfish/v1/UpdateService/FirmwareInventory/Previous-159-2.3.10
    """
    etag = _get_fw_etag(uri)
    headers = {"If-Match": "{ETag}".format(ETag=etag)}
    return __proxy__["redfish.http_delete"](uri, headers=headers)


def _get_fw_etag(uri):
    logging.debug({"uri": uri})
    details = __proxy__["redfish.get_details"]()
    session = details["session"]
    host = details["host"]
    inventory = session.get("https://" + host + uri)
    logging.debug({"ETag": inventory.headers["ETag"]})
    return inventory.headers["ETag"]


# Module to download and copy the content of the file to specified path
def download_firmware(uri, md5hash):
    """
    Whenever we find a new software version of a particular component, to update that
    first we download it to a specific path and then install it.

    Param:
        -url: Here, the url from where the software is to be downloaded will be present

    Return: Displays whether the action is sucessful or not

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.download_firmware url="Path where the file to be downloaded is present"
    """
    response = requests.get("http://downloads.dell.com/" + uri, verify=False)
    try:
        file_path = "/opt/" + os.path.basename(uri)
        with salt.utils.files.fopen(file_path, "wb") as fw_payload_file:
            fw_payload_file.write(response.content)
        md5sum = hashlib.md5(pathlib.Path(file_path).read_bytes()).hexdigest()
        if md5sum == md5hash:
            return {"result": True, "path": file_path}
    except requests.exceptions.RequestException:
        return {"result": False,"comment": "Not able to download Firmware"}


def upload_firmware(path):
    """
    This module provide functionality to upload firmware to system

    Param:
        -path: local path to firmware

    Return: status of firmware upload

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.upload_firmware path=/tmp/FW/BIOS-1.0.0.EXE
    """
    etag = _get_fw_etag("/redfish/v1/UpdateService/FirmwareInventory/")
    files = {
        "file": (
            os.path.basename(path),
            salt.utils.files.fopen(path, "rb"),
            "multipart/form-data",
        )
    }
    headers = {"if-match": "{ETag}".format(ETag=etag)}
    return __proxy__["redfish.http_post"](
        "/redfish/v1/UpdateService/FirmwareInventory", files=files, headers=headers
    )


# Module to update the firmware
def update_firmware(uri):
    """
    This module is used to update the firmware of the component specified by the user if updated version is found in the repository.
    Here, the updated version of firmware is uploaded in to the payload and will be installed on to the system.

    Params:
        - uri: path where the latest version of the component is present

    Return: Displays whether the action is sucessful or not

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.update_firmware path="Path where the file to be installed is present"
    """
    payload = {"ImageURI": uri}
    headers = {"content-type": "application/json"}
    update = __proxy__["redfish.http_post"](
        "/redfish/v1/UpdateService/Actions/UpdateService.SimpleUpdate",
        headers=headers,
        payload=payload,
    )
    return update


# Module to check status of the specified job
def check_job_status(job_id):
    """
    This is used to check the status of the job specified by the user.

    Param:
        - job_id: JID of the job whose status is to be checked

    Return: Displays whether the action is sucessful or not

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.check_job_status job_id="JID of the job"
    """
    config = __opts__["redfish"]

    while True:
        uri = "/redfish/v1/TaskService/Tasks/"
        req = requests.get(
            config["redfish_ip"] + uri + job_id,
            auth=(config["username"], config["password"]),
            verify=False,
        )
        data = req.json()
        status_code = req.status_code

        if status_code != 202 or status_code != 200:
            return {"result": False, "message": "Query job ID command failed"}
        return {"result": True, "message": data["TaskState"]}

    return {"result": False, "message": "Nothing executed"}


# Module to reboot server
def system_reboot_server():
    """
    This module is used to reboot the server based on the user requirement.
    For some of the updates in the system to be installed, it requires reboot.
    At that time user can execute this module.

    Return: Displays whether the action is sucessful or not

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_reboot_server
    """
    uri = "/redfish/v1/Systems/System.Embedded.1/"
    config = __opts__["redfish"]
    response = requests.get(
        config["redfish_ip"] + uri,
        auth=(config["username"], config["password"]),
        verify=False,
    )
    data = response.json()

    if data["PowerState"] == "On":
        url = (
            config["redfish_ip"]
            + "/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset"
        )
        payload = {"ResetType": "GracefulShutdown"}
        headers = {"content-type": "application/json"}
        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=headers,
            verify=False,
            auth=(config["username"], config["password"]),
        )
        status_code = response.status_code
        if status_code != 204:
            return {
                "result": False,
                "message": "Command failed to gracefully power OFF server",
            }
        time.sleep(10)
        count = 0
        while True:
            response = requests.get(
                config["redfish_ip"] + "/redfish/v1/Systems/System.Embedded.1/",
                verify=False,
                auth=(config["username"], config["password"]),
            )
            data = response.json()
            if data["PowerState"] == "Off":
                break
            elif count == 20:
                url = (
                    config["redfish_ip"]
                    + "/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset"
                )
                payload = {"ResetType": "ForceOff"}
                headers = {"content-type": "application/json"}
                response = requests.post(
                    url,
                    data=json.dumps(payload),
                    headers=headers,
                    verify=False,
                    auth=(config["username"], config["password"]),
                )
                status_code = response.status_code
                if status_code != 204:
                    return {
                        "result": False,
                        "message": "FAIL, Command failed to gracefully power OFF server",
                    }
                time.sleep(15)
                break
            else:
                time.sleep(2)
                count += 1
                continue

        payload = {"ResetType": "On"}
        headers = {"content-type": "application/json"}
        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=headers,
            verify=False,
            auth=(config["username"], config["password"]),
        )
        status_code = response.status_code
        if status_code != 204:
            return {
                "result": False,
                "message": "- FAIL, Command failed to power ON server",
            }

    elif data["PowerState"] == "Off":
        url = (
            config["redfish_ip"]
            + "/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset"
        )
        payload = {"ResetType": "On"}
        headers = {"content-type": "application/json"}
        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=headers,
            verify=False,
            auth=(config["username"], config["password"]),
        )
        status_code = response.status_code
        if status_code != 204:
            return {
                "result": False,
                "message": "- FAIL, Command failed to power ON server",
            }

        return {"result": True, "message": "passed"}

    else:
        return {
            "result": False,
            "message": "- FAIL, unable to get current server power state to perform either reboot or power on",
        }


def system_get_bios_attribute_type(attribute_name):
    """
    This is used to get BIOS attribute types

    Params:
        - attribute_names: BIOS attributes name

    Return: Displays BIOS attribute type

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_get_bios_attribute_type attribute_names="BootMode"
    """

    bios_registry = __proxy__["redfish.http_get"](
        "/redfish/v1/Systems/System.Embedded.1/Bios/BiosRegistry"
    )
    if bios_registry:
        if "RegistryEntries" in bios_registry:
            if "Attributes" in bios_registry["RegistryEntries"]:
                for attrib in bios_registry["RegistryEntries"]["Attributes"]:
                    if attrib["AttributeName"] == attribute_name:
                        return attrib["Type"]
    return bios_registry


def system_get_bios_attribute_current_value(attribute_name):
    """
    This is used to get BIOS attribute current value

    Params:
        - attribute_names: BIOS attribute name

    Return: Displays BIOS attribute current value 

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_get_bios_attribute_current_value attribute_names="BootMode"
    """

    bios_attributes = __proxy__["redfish.http_get"](
        "/redfish/v1/Systems/System.Embedded.1/Bios/"
    )
    if bios_attributes:
        if "Attributes" in bios_attributes:
            if attribute_name in bios_attributes["Attributes"]:
                return bios_attributes["Attributes"][attribute_name]
    return False


# Module to set the bios attributes
def system_set_bios_attribute(attribute_names=[], attribute_values=[]):
    """
    This is used to change the bios attributes based on the user requirement by specifying the
    attributes to be changed along with the values respectively.

    Params:
        - attribute_names: list of the attributes whose values are to be changed
        - attribute_values: list of values for corresponding attributes

    Return: Displays whether the action is sucessful or not

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_set_bios_attributes attribute_names=["BootMode"]
                                                            attribute_values=["Uefi"]
    """

    payload = {"Attributes": {}}
    for attri_name, attri_val in zip(attribute_names, attribute_values):
        attrib_type = system_get_bios_attribute_type(attri_name)
        if attrib_type == "Integer":
            payload["Attributes"][attri_name] = int(attri_val)
        else:
            payload["Attributes"][attri_name] = attri_val
    logging.debug(payload)
    headers = {"content-type": "application/json"}
    bios_uri = "/redfish/v1/Systems/System.Embedded.1/Bios/Settings"
    bios_set = __proxy__["redfish.http_patch"](bios_uri, headers, payload)
    if bios_set:
        job_uri = "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs"
        payload = {
            "TargetSettingsURI": "/redfish/v1/Systems/System.Embedded.1/Bios/Settings"
        }
        headers = {"content-type": "application/json"}
        config_job = __proxy__["redfish.http_post"](job_uri, headers, payload)
        if config_job:
            logging.debug(config_job["headers"]["Location"])
            job_id = config_job["headers"]["Location"]
            restart = system_reset(reset_type="ForceRestart")
            if restart:
                for i in range(20):
                    job_status = bios_set = __proxy__["redfish.http_get"](job_id)
                    if job_status["JobState"] == "Completed":
                        return { "result": True, "message": "BIOS Attribute set successfully", }
                    time.sleep(30)

    return {
        "result": False,
        "message": "Attribute set failed",
        "StatusCode": False,
    }


# Module to create virtual disk
def system_create_virtual_disk(controller, disks, volume_type):
    """
    This module is used to create the RAID levels with the help of the physical drives present.

    Params:
        - controller: storage controller on which virtual disk is to be created
        - disks: It is a string of disks separated by comma(,) to create RAID levels
        - volume_type: to define the type of RAID level

    Return: Displays whether the action is sucessful or not

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_create_virtual_disk controller="contoller that supports RAID creation"
                                        disks="Disks for creation" volume_type:"Type of RAID to be created"
    """
    config = __opts__["redfish"]
    url = "/redfish/v1/Systems/System.Embedded.1/Storage/" + controller
    disks_list = disks.split(",")
    final_disks_list = []
    for i in disks_list:
        drives_uri = "/redfish/v1/Systems/System.Embedded.1/Storage/Drives/" + i
        drive_id = {"@odata.id": drives_uri}
        final_disks_list.append(drive_id)
    payload = {"VolumeType": volume_type, "Drives": final_disks_list}

    headers = {"Content-type": "application/json"}
    response = requests.post(
        config["redfish_ip"] + url + "/Volumes",
        data=json.dumps(payload),
        headers=headers,
        verify=False,
        auth=(config["username"], config["password"]),
    )
    if response.status_code == 202:
        pass
    else:
        return {"result": False, "message": "Post command failed to execute"}

    resp_header = response.headers["Location"]
    try:
        job_id = re.search("JID.+", resp_header).group()
    except KeyError:
        return {"result": False, "message": "Job_ID creation failed"}

    req = requests.get(
        config["redfish_ip"] + "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/" + job_id,
        auth=(config["username"], config["password"]),
        verify=False,
    )
    data = req.json()
    if data["JobType"] == "RAIDConfiguration":
        job_type = "staged"
    elif data["JobType"] == "RealTimeNoRebootConfiguration":
        job_type = "realtime"
    return {"result": True, "Job_ID": job_id, "JobType": job_type}


# Module to delete virtual disk
def system_delete_virtual_disk(fqdd):
    """
    This module is used to delete the virtual disks created for RAID.

    Params:
        - fqdd: provide the details of the virtual disk to be deleted

    Return: Displays whether the action is sucessful or not

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.ssytem_delete_virtual_disk fqdd="virtual disk details"
    """
    config = __opts__["redfish"]
    url = "/redfish/v1/Systems/System.Embedded.1/Storage/Volumes/"
    response = requests.delete(
        config["redfish_ip"] + url + fqdd,
        verify=False,
        auth=(config["username"], config["password"]),
    )

    if response.status_code == 202:
        pass
    else:
        return {
            "result": False,
            "message": "Delete command failed",
            "status_code": response.json(),
        }

    resp_header = response.headers["Location"]
    try:
        job_id = re.search("JID.+", resp_header).group()
    except KeyError:
        return {"result": False, "message": "Job_ID failed to create"}

    req = requests.get(
        config["redfish_ip"] + "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/" + job_id,
        auth=(config["username"], config["password"]),
        verify=False,
    )
    data = req.json()
    if data["JobType"] == "RAIDConfiguration":
        job_type = "staged"
    elif data["JobType"] == "RealTimeNoRebootConfiguration":
        job_type = "realtime"
    return {"result": True, "Job_ID": job_id, "Job_type": job_type}


def system_get_pdisks_hot_spare_type(fqdd):
    """
    This module is used to physical disks of hot spare type.

    Params:
        - fqdd: provide the details of the virtual disk

    Return: Displays whether the action is sucessful or not

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_get_pdisks_hot_spare_type fqdd="virtual disk details"
    """
    config = __opts__["redfish"]
    url = "/redfish/v1/Systems/System.Embedded.1/Storage/"
    response = requests.get(
        config["redfish_ip"] + url + "/" + fqdd,
        verify=False,
        auth=(config["username"], config["password"]),
    )
    if response.status_code != 200:
        return {
            "result": False,
            "message": "Either controller fqdd does not exist or typo in fqdd string name",
        }
    data = response.json()
    drive_list = []
    if data["Drives"] != []:
        for i in data["Drives"]:
            for drive_name in i.items():
                disk = drive_name[1].split("/")[-1]
                drive_list.append(disk)
    else:
        return {"result": False, "message": "No drives found for specified controller"}

    drive_types = {}
    for i in drive_list:
        response = requests.get(
            config["redfish_ip"]
            + "/redfish/v1/Systems/System.Embedded.1/Storage/Drives/"
            + i,
            verify=False,
            auth=(config["username"], config["password"]),
        )
        data = response.json()
        for hotspare_type in data.items():
            if hotspare_type[0] == "HotspareType":
                drive_types[i] = hotspare_type[1]
    return {"result": True, "Spare_type": drive_types}


# Module to assign hot spare
def system_assign_spare(types, hot_spare, virtual_disk):
    """
    This module is used to assign hot spare to VD

    Params:
        - type: provide type of assign like global or dedicated
        - hot_spare: fqdd of physical disk
        - virtual_disk: fqdd of virtual disk
    Return: Displays whether the action is sucessful or not

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_assign_spare types=dedicated hot_spare=Slot-1.0.1 virtual_disk=<fqdd>
    """

    config = __opts__["redfish"]
    url = "/redfish/v1/Dell/Systems/System.Embedded.1/DellRaidService/Actions/DellRaidService.AssignSpare"
    headers = {"content-type": "application/json"}

    if types.lower() == "global":
        payload = {"Targetfqdd": hot_spare}
    elif types.lower() == "dedicated":
        payload = {"Targetfqdd": hot_spare, "VirtualDiskArray": [virtual_disk]}

    response = requests.post(
        config["redfish_ip"] + url,
        data=json.dumps(payload),
        headers=headers,
        verify=False,
        auth=(config["username"], config["password"]),
    )
    if response.status_code == 202:
        try:
            job_id = response.headers["Location"].split("/")[-1]
        except KeyError:
            return {"result": False, "message": "Unable to find Job_ID"}
        return {"result": True, "Job_ID": job_id}

    return {"result": False, "message": "Unable to execute post command"}


# Module to get the job ids in iDRAC job queue
def manager_get_jobs():
    """
    This is used to get all the job ids present in the job queue of the iDRAC

    Return: Job IDs present in the system

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.manager_get_job_queue_ids
    """
    jobs = __proxy__["redfish.http_get"]("/redfish/v1/Managers/iDRAC.Embedded.1/Jobs")
    if jobs:
        return jobs
    return False


# Module to get the details of job
def manager_get_job_detail(job_id):
    """
    This is used to get the details of specified job present in the job queue of the iDRAC

    Param:
        - job_id: JID of the job whose details are required

    Return: Dictionary displaying the details of the specified job

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.manager_get_job_id_details job_id="JID of job"
    """
    job_detail = __proxy__["redfish.http_get"](
        "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/" + job_id
    )
    if job_detail:
        return job_detail
    return job_detail


# Module to delete the job
def manager_delete_job_id(job_id):
    """
    This is used to delete the specified job, if present in the job queue of iDRAC

    Param:
        - job_id: JID of the job which is to be deleted

    Return: Displays whether the action is sucessful or not

    CLI Example:
    .. code-block:: bash
        salt '*' redfish.manager_delete_job_id job_id="JID of job"
    """
    headers = {"content-type": "application/json"}
    job_del = __proxy__["redfish.http_delete"](
        "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/" + job_id, headers=headers
    )
    return job_del


# Module to clear all the jobs
def manager_clear_jobs():
    """
    This is used to delete all the jobs present in the job queue of iDRAC

    Return: Displays whether the action is sucessful or not

    CLI Example:
    .. code-block:: bash
        salt '*' redfish.manager_clear_job_queue
    """
    jobs = __proxy__["redfish.http_get"]("/redfish/v1/Managers/iDRAC.Embedded.1/Jobs")
    if jobs:
        for job_id in jobs["Members"]:
            headers = {"content-type": "application/json"}
            job_d = __proxy__["redfish.http_delete"](
                job_id["@odata.id"], headers=headers
            )
            if job_d:
                continue
            return job_d
    return {"result": True, "message": "Job queue is cleared successfully"}


def manager_get_sessions():
    """
    This function is used to get number of sessions with system manager


    Return: Display number of session

    CLI Example:
    .. code-block:: bash
        salt '*' redfish.manager_get_sessions
    """

    session = __proxy__["redfish.http_get"]("/redfish/v1/SessionService/Sessions/")
    if "Members" in session:
        return session["Members"]
    return session


def manager_get_host_interfaces():
    """
    This function provide list host interfaces


    Return: Display number of host interfaces

    CLI Example:
    .. code-block:: bash
        salt '*' redfish.manager_get_host_interfaces
    """

    host_interfaces = __proxy__["redfish.http_get"](
        "/redfish/v1/Managers/iDRAC.Embedded.1/HostInterfaces"
    )
    if host_interfaces:
        return host_interfaces["Members"]
    return host_interfaces
