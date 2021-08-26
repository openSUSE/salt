# -*- coding: utf-8 -*-
"""
DMTF Redfish API for managing server
The redfish  module is used to create and manage  servers through out of band interface

"""
# Import Python Libs
from __future__ import absolute_import, print_function, unicode_literals
import logging


# Import Salt Libs
import salt.utils.json
import salt.utils.versions


log = logging.getLogger(__name__)


def __virtual__():
    """
    Only load if the bower module is available in __salt__
    """
    return "redfish"


def default_bios_settings(name):
    """
    Set factory default settings of BIOS
    Return: dictonory of result

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.default_bios_settings


    """
    ret = {"name": name, "result": False, "comment": "bios reset faild", "changes": {}}
    if __opts__["test"]:
        ret["comment"] = "Reset BIOS setting to Default"
        ret["result"] = None
        return ret

    bios_reset = __salt__["redfish.system_bios_reset_to_default"]()
    if bios_reset:
        ret["result"] = True
        ret["comment"] = "system bios reset to factory default"
        ret["changes"]["ForceRestart"] = "In Progress"
        ret["changes"]["BIOS"] = "Factory Default"
        return ret
    return ret


def system_power_state(name, power_state):
    """
    set system power state
    Params:
        - power_state : set power state
    Return: dictonory of result

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_power_state


    """

    ret = {"name": name, "result": False, "comment": "bios reset faild", "changes": {}}
    if __opts__["test"]:
        ret["comment"] = "Set Power state to {0}".format(power_state)
        ret["result"] = None
        return ret

    if power_state not in ["On", "Off"]:
        ret["comment"] = "power state type not avaiable. supported options On|Off"
    else:
        sys_info = __salt__["redfish.get_system_info"]()
        if sys_info:
            logging.debug(sys_info["PowerState"])
            if power_state == sys_info["PowerState"]:
                ret["result"] = True
                ret["comment"] = "Already system  in power {power_state} state".format(
                    power_state=power_state
                )
            elif power_state == "On":
                if __salt__["redfish.system_reset"](reset_type="On"):
                    ret["comment"] = "Powering on system"
                    ret["changes"]["PowerState"] = "On"
                    ret["result"] = True
            elif power_state == "Off":
                if __salt__["redfish.system_reset"](reset_type="ForceOff"):
                    ret["comment"] = "Powering off system"
                    ret["changes"]["PowerState"] = "Off"
                    ret["result"] = True
    return ret


def bios_mode_to_uefi(name):
    """
    This state will set BIOS boot mode to UEFI

    Return: dictonory of result

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.bios_mode_to_uefi"
    """

    ret = {
        "name": name,
        "result": False,
        "comment": "faild to set UEFI mode",
        "changes": {},
    }
    if __opts__["test"]:
        ret["comment"] = "Set to UEFI mode "
        ret["result"] = None
        return ret

    bios_info = __salt__["redfish.system_get_bios_attributes"]()
    if "Attributes" in bios_info:
        if "BootMode" in bios_info["Attributes"]:
            logging.debug(bios_info)
            logging.debug(bios_info["Attributes"]["BootMode"])
            if bios_info["Attributes"]["BootMode"] == "Uefi":
                ret["comment"] = "Already in UEFI Mode"
                ret["result"] = True
                return ret
            else:
                bios_mode = __salt__["redfish.system_set_bios_attribute"](
                    attribute_names=["BootMode"], attribute_values=["Uefi"]
                )
                if bios_mode:
                    if "Job_id" in bios_mode:
                        status = __salt__["redfish.check_job_status"]()
                        logging.debug(status)


def nic_pxe_configure(name, nic_fqdd):
    """
    This state will be used to set system one time boot to device
    Params:
        - boot_mode : system boot mode used for one time boot
        - boot_device : device name for one time boot

    Return: dictonory of result

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_onetime_boot boot_mode="Bios" boot_device="Pxe"
    """
    ret = {
        "name": name,
        "result": False,
        "comment": "NIC FQDD not exist",
        "changes": {},
    }
    if __opts__["test"]:
        ret["comment"] = "NIC for PXE boot {0}".format(boot_device)
        ret["result"] = None
        return ret
    nic_adaptors = __salt__["redfish.system_get_ethernet_devices"]()
    if nic_fqdd in nic_adaptors:
        logging.debug("Requested Network Controller Exist: " + nic_fqdd)
        if nic_adaptors[nic_fqdd]["LinkStatus"] != "LinkUp":

            ret["comment"] = "Network Port cable not connected"
            ret["result"] = False
            return ret
        logging.debug("Requested Network Controller Cable Connected: " + nic_fqdd)
        nic_name = nic_fqdd.split("-")[0]
        logging.error("prabhakar" + nic_name)
        nic_func = __salt__["redfish.system_get_network_adapter_device_functions"](
            nic_name
        )
        if "Oem" in nic_func[nic_fqdd]:
            logging.debug(nic_func[nic_fqdd])
            if (
                nic_func[nic_fqdd]["Oem"]["Dell"]["DellNICCapabilities"][
                    "PXEBootSupport"
                ]
                == "Supported"
            ):
                logging.debug("Requested Network Controller Support PXE: " + nic_fqdd)
                attrib = '["PxeDev1EnDis","PxeDev1Interface", "PxeDev1Protocol","PxeDev1VlanEnDis"]'
                attrib_value = '["Enabled",' + nic_fqdd + ',"IPv4","Disabled"]'
                logging.debug("attributes:")
                logging.debug(attrib)

                logging.debug("attribute values:")
                logging.debug(attrib_value)

                pxe_config = __salt__["redfish.system_set_bios_attribute"](
                    attribute_names=attrib, attribute_values=attrib_value
                )
                if pxe_config:
                    ret["comment"] = "Pass"
                    ret["result"] = True
    return ret


def system_onetime_boot_uefi(name, boot_device):
    """
    This state will be used to set system one time boot to device
    Params:
        - boot_mode : system boot mode used for one time boot
        - boot_device : device name for one time boot

    Return: dictonory of result

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_onetime_boot boot_mode="Bios" boot_device="Pxe"

    """

    ret = {"name": name, "result": False, "comment": "Wrong reset type", "changes": {}}
    if __opts__["test"]:
        ret["comment"] = "OneTime boot set to device {0}".format(boot_device)
        ret["result"] = None
        return ret
    status = __salt__["redfish.system_onetime_boot_device_uefi"](boot_device)
    if status:
        ret["result"] = True
        ret["comment"] = "set One Time Boot to {boot_device}".format(
            boot_device=boot_device
        )
        return ret
    else:
        ret["comment"] = "ForceRestart Failed"
        ret["result"] = False
        return ret


def virtual_media_attached(name, url, force=False):
    """
    set system power state
    Params:
        - power_state : set power state
    Return: dictonory of result

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_power_state


    """
    ret = {
        "name": name,
        "result": False,
        "comment": "Virtual Media Attach faild",
        "changes": {},
    }
    if __opts__["test"]:
        ret["comment"] = "virtual media attached {0}".format(url)
        ret["result"] = None
        return ret

    media = __salt__["redfish.manager_get_virtual_media_cd"]()
    if "Inserted" in media:
        if media["Image"] == url:
            ret["result"] = True
            ret["comment"] = "{url} already attached".format(url=url)
        else:
            media = __salt__["redfish.manager_attach_cd"](url, force)
            if media:
                ret["result"] = True
                ret["comment"] = "{url} attached".format(url=url)
                ret["changes"]["iso"] = url
    return ret


def virtual_removable_disk_attached(name, url, force=False):
    """
    set system power state
    Params:
        - power_state : set power state
    Return: dictonory of result

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_power_state


    """

    ret = {
        "name": name,
        "result": False,
        "comment": "Virtual Media Attach faild",
        "changes": {},
    }
    if __opts__["test"]:
        ret["comment"] = "Removable Disk attached {0}".format(url)
        ret["result"] = None
        return ret
    media = __salt__["redfish.manager_get_virtual_media_removable_disk"]()
    if "Inserted" in media:
        if media["Image"] == url:
            ret["result"] = True
            ret["comment"] = "{url} already attached".format(url=url)
        else:
            media = __salt__["redfish.manager_attach_removable_disk"](url, force)
            if media:
                ret["result"] = True
                ret["comment"] = "{url} attached".format(url=url)
                ret["changes"]["iso"] = url
    return ret


def one_time_boot(name, media):
    """
    set system power state
    Params:
        - power_state : set power state
    Return: dictonory of result

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_power_state


    """

    ret = {"name": name, "result": False, "comment": "bios reset faild", "changes": {}}
    if __opts__["test"]:
        ret["comment"] = "one time boot into {0}".format(media)
        ret["result"] = None
        return ret
    boot_options = __salt__["redfish.system_get_current_boot_devices"]()
    if boot_options and media in boot_options:
        onetime = __salt__["redfish.system_onetime_boot"](
            boot_mode="Uefi", boot_device="Pxe"
        )
        if onetime:
            reset = __salt__["redfish.system_reset"](reset_type="ForceRestart")
            if reset:
                ret["result"] = True
                ret["changes"]["onetimeBoot"] = media
                ret["comment"] = "one time booting into {media}".format(media=media)
    return ret


def check_firmware_update(name):
    """
    set system power state
    Params:
        - power_state : set power state
    Return: dictonory of result

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_power_state


    """

    updates = {}
    ret = {
        "name": name,
        "result": False,
        "comment": "Firmware update check failed",
        "changes": {},
    }
    if __opts__["test"]:
        ret["comment"] = "checking firmware to update"
        ret["result"] = None
        return ret
    components = __salt__["redfish.update_service_get_fw_components"](
        comp_type="Installed"
    )
    sysinfo = __salt__["redfish.get_system_info"]()
    if "Model" in sysinfo:
        model = sysinfo["Model"].split(" ")[1]
        latest_fws = __salt__["redfish.parse_catalogue_file"](model, components)
        current_fws = __salt__["redfish.get_installed_version"](components)
        for i in current_fws.keys():
            if (
                salt.utils.versions.version_cmp(
                    latest_fws[i]["version"], current_fws[i]["version"]
                )
                == 1
            ):
                updates[i] = {
                    "name": current_fws[i]["name"],
                    "Current Version": current_fws[i]["version"],
                    "Latest Version": latest_fws[i]["version"],
                    "path": latest_fws[i]["path"],
                }
        ret["result"] = True
        ret["changes"] = updates
        ret["comment"] = "Firmware check is successful"
    return ret


def firmware_update_to_latest(name):
    """
    set system power state
    Params:
        - power_state : set power state
    Return: dictonory of result

    CLI Example:
    .. code-block:: bash
                salt '*' redfish.system_power_state


    """

    ret = {
        "name": name,
        "result": False,
        "comment": "Firmware update failed",
        "changes": {},
    }
    if __opts__["test"]:
        ret["comment"] = "update firmware to latest"
        ret["result"] = None
        return ret
    components = __salt__["redfish.update_service_get_fw_components"](
        comp_type="Installed"
    )
    sysinfo = __salt__["redfish.get_system_info"]()
    if "Model" in sysinfo:
        model = sysinfo["Model"].split(" ")[1]
        latest_fws = __salt__["redfish.parse_catalogue_file"](model, components)
        current_fws = __salt__["redfish.get_current_version"](components)
        for i in current_fws.keys():
            if (
                salt.utils.versions.version_cmp(
                    latest_fws[i]["version"], current_fws[i]["version"]
                )
                == 1
            ):
                download = __salt__["redfish.download_firmware"](
                    latest_fws[i]["path"], latest_fws[i]["hashMD5"]
                )
                if download["result"] and latest_fws[i]["rebootRequired"] == "false":
                    upload_fw = __salt__["redfish.upload_firmware"](download["path"])
                    upload_fw = __salt__["redfish.update_firmware"](
                        upload_fw["data"]["@odata.id"]
                    )
                    break
        ret["changes"] = upload_fw
        ret["result"] = True

    return ret
