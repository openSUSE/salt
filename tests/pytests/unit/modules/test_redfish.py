import os.path
import pytest
import salt.modules.redfish as redfish
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def setup_loader():
    setup_loader_modules = {redfish: {"__proxy__": {}}}
    with pytest.helpers.loader_mock(setup_loader_modules) as loader_mock:
        yield loader_mock


def test_system_get_current_boot_devices():

    ret = [
        "None",
        "Pxe",
        "Floppy",
        "Cd",
        "Hdd",
        "BiosSetup",
        "Utilities",
        "UefiTarget",
        "SDCard",
        "UefiHttp",
    ]
    mock = MagicMock(
        return_value={
            "Boot": {
                "BootSourceOverrideTarget@Redfish.AllowableValues": [
                    "None",
                    "Pxe",
                    "Floppy",
                    "Cd",
                    "Hdd",
                    "BiosSetup",
                    "Utilities",
                    "UefiTarget",
                    "SDCard",
                    "UefiHttp",
                ]
            }
        }
    )

    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.system_get_current_boot_devices() == ret


def test__system_get_reset_type():

    ret = [
        "On",
        "ForceOff",
        "ForceRestart",
        "GracefulShutdown",
        "PushPowerButton",
        "Nmi",
    ]
    mock = MagicMock(
        return_value={
            "Actions": {
                "#ComputerSystem.Reset": {
                    "ResetType@Redfish.AllowableValues": [
                        "On",
                        "ForceOff",
                        "ForceRestart",
                        "GracefulShutdown",
                        "PushPowerButton",
                        "Nmi",
                    ]
                }
            }
        }
    )
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.system_get_reset_type() == ret


def test__system_get_boot_options():
    mock = MagicMock(
        return_value={
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/BootOptions/Boot0000"
                }
            ]
        }
    )

    ret = {
        "Boot0000": {
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/BootOptions/Boot0000"
                }
            ]
        }
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.system_get_boot_options() == ret


def test__system_get_PSU_info():
    ret = {
        "PSU.Slot.1": {
            "Links": {
                "PoweredBy": [
                    {
                        "@odata.id": "/redfish/v1/Chassis/System.Embedded.1/Power/PowerSupplies/PSU.Slot.1"
                    }
                ]
            }
        }
    }
    mock = MagicMock(
        return_value={
            "Links": {
                "PoweredBy": [
                    {
                        "@odata.id": "/redfish/v1/Chassis/System.Embedded.1/Power/PowerSupplies/PSU.Slot.1"
                    }
                ]
            }
        }
    )

    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.system_get_PSU_info() == ret


def test__system_get_chassis_cooling_devices():
    ret = {
        "0x17%7C%7CFan.Embedded.1": {
            "Links": {
                "CooledBy": [
                    {
                        "@odata.id": "/redfish/v1/Chassis/System.Embedded.1/Sensors/Fans/0x17%7C%7CFan.Embedded.1"
                    }
                ]
            }
        }
    }
    mock = MagicMock(
        return_value={
            "Links": {
                "CooledBy": [
                    {
                        "@odata.id": "/redfish/v1/Chassis/System.Embedded.1/Sensors/Fans/0x17%7C%7CFan.Embedded.1"
                    }
                ]
            }
        }
    )
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.system_get_chassis_cooling_devices() == ret


def test__system_get_processor_info():
    ret = {
        "CPU.Socket.1": {
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/Processors/CPU.Socket.1"
                }
            ]
        }
    }
    mock = MagicMock(
        return_value={
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/Processors/CPU.Socket.1"
                }
            ]
        }
    )
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.system_get_processor_info() == ret


def test__system_get_secureboot_info():
    ret = {
        "Actions": {
            "#SecureBoot.ResetKeys": {
                "ResetKeysType@Redfish.AllowableValues": [
                    "ResetAllKeysToDefault",
                    "DeleteAllKeys",
                    "DeletePK",
                    "ResetPK",
                    "ResetKEK",
                    "ResetDB",
                    "ResetDBX",
                ]
            }
        }
    }
    mock = MagicMock(
        return_value={
            "Actions": {
                "#SecureBoot.ResetKeys": {
                    "ResetKeysType@Redfish.AllowableValues": [
                        "ResetAllKeysToDefault",
                        "DeleteAllKeys",
                        "DeletePK",
                        "ResetPK",
                        "ResetKEK",
                        "ResetDB",
                        "ResetDBX",
                    ]
                }
            }
        }
    )
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.system_get_secureboot_info() == ret


def test__system_get_storage_controllers_info():
    mock = MagicMock(
        return_value={
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/Storage/RAID.Slot.1-1"
                },
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/Storage/AHCI.Embedded.1-1"
                },
            ]
        }
    )
    ret = {
        "RAID.Slot.1-1": {
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/Storage/RAID.Slot.1-1"
                },
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/Storage/AHCI.Embedded.1-1"
                },
            ]
        },
        "AHCI.Embedded.1-1": {
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/Storage/RAID.Slot.1-1"
                },
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/Storage/AHCI.Embedded.1-1"
                },
            ]
        },
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.system_get_storage_controllers_info() == ret


def test__get_lc_logs():
    mock = MagicMock(
        return_value={
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/Logs/Lclog/141673",
                    "@odata.type": "#LogEntry.v1_3_0.LogEntry",
                    "Created": "2020-10-07T05:02:44-05:00",
                    "Description": " Log Entry 141673",
                    "EntryType": "Oem",
                    "Id": "141673",
                    "Links": {
                        "OriginOfCondition": {
                            "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1"
                        }
                    },
                    "Message": "Successfully logged in using root, from 10.107.68.191 and REDFISH.",
                    "MessageArgs": ["root", "10.107.68.191", "REDFISH"],
                    "MessageArgs@odata.count": 3,
                    "MessageId": "USR0030",
                    "Name": " Log Entry 141673",
                    "OemRecordFormat": "Dell",
                    "Severity": "OK",
                }
            ]
        }
    )

    ret = {
        "Members": [
            {
                "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/Logs/Lclog/141673",
                "@odata.type": "#LogEntry.v1_3_0.LogEntry",
                "Created": "2020-10-07T05:02:44-05:00",
                "Description": " Log Entry 141673",
                "EntryType": "Oem",
                "Id": "141673",
                "Links": {
                    "OriginOfCondition": {
                        "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1"
                    }
                },
                "Message": "Successfully logged in using root, from 10.107.68.191 and REDFISH.",
                "MessageArgs": ["root", "10.107.68.191", "REDFISH"],
                "MessageArgs@odata.count": 3,
                "MessageId": "USR0030",
                "Name": " Log Entry 141673",
                "OemRecordFormat": "Dell",
                "Severity": "OK",
            }
        ]
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.get_lc_logs() == ret


def test__get_sel_logs():
    mock = MagicMock(
        return_value={
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/Logs/Sel/795",
                    "@odata.type": "#LogEntry.v1_3_0.LogEntry",
                    "Created": "2020-10-06T06:29:23-05:00",
                    "Description": " Log Entry 795",
                    "EntryCode": "Deassert",
                    "EntryType": "SEL",
                    "Id": "795",
                    "Links": {},
                    "Message": "The chassis is closed while the power is off.",
                    "MessageArgs": [],
                    "MessageArgs@odata.count": 0,
                    "MessageId": "802ff",
                    "Name": " Log Entry 795",
                    "SensorNumber": 115,
                    "SensorType": "Physical Chassis Security",
                    "Severity": "OK",
                }
            ]
        }
    )
    ret = {
        "Members": [
            {
                "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/Logs/Sel/795",
                "@odata.type": "#LogEntry.v1_3_0.LogEntry",
                "Created": "2020-10-06T06:29:23-05:00",
                "Description": " Log Entry 795",
                "EntryCode": "Deassert",
                "EntryType": "SEL",
                "Id": "795",
                "Links": {},
                "Message": "The chassis is closed while the power is off.",
                "MessageArgs": [],
                "MessageArgs@odata.count": 0,
                "MessageId": "802ff",
                "Name": " Log Entry 795",
                "SensorNumber": 115,
                "SensorType": "Physical Chassis Security",
                "Severity": "OK",
            }
        ]
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.get_sel_logs() == ret


def test__get_fault_logs():
    mock = MagicMock(return_value={"Members": []})
    ret = {"Members": []}
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.get_fault_logs() == ret


def test__manager_get_virtual_media_removable_disk():
    mock = MagicMock(
        return_value={
            "Actions": {
                "#VirtualMedia.EjectMedia": {
                    "target": "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/RemovableDisk/Actions/VirtualMedia.EjectMedia"
                },
                "#VirtualMedia.InsertMedia": {
                    "target": "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/RemovableDisk/Actions/VirtualMedia.InsertMedia"
                },
            }
        }
    )
    ret = {
        "Actions": {
            "#VirtualMedia.EjectMedia": {
                "target": "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/RemovableDisk/Actions/VirtualMedia.EjectMedia"
            },
            "#VirtualMedia.InsertMedia": {
                "target": "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/RemovableDisk/Actions/VirtualMedia.InsertMedia"
            },
        }
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.manager_get_virtual_media_removable_disk() == ret


def test__manager_get_virtual_media_cd():
    mock = MagicMock(
        return_value={
            "Actions": {
                "#VirtualMedia.EjectMedia": {
                    "target": "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/CD/Actions/VirtualMedia.EjectMedia"
                },
                "#VirtualMedia.InsertMedia": {
                    "target": "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/CD/Actions/VirtualMedia.InsertMedia"
                },
            }
        }
    )

    ret = {
        "Actions": {
            "#VirtualMedia.EjectMedia": {
                "target": "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/CD/Actions/VirtualMedia.EjectMedia"
            },
            "#VirtualMedia.InsertMedia": {
                "target": "/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia/CD/Actions/VirtualMedia.InsertMedia"
            },
        }
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.manager_get_virtual_media_cd() == ret


def test__system_get_network_adapters():
    mock = MagicMock(
        return_value={
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/NetworkAdapters/NIC.Embedded.1"
                }
            ]
        }
    )
    ret = {
        "NIC.Embedded.1": {
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/NetworkAdapters/NIC.Embedded.1"
                }
            ]
        }
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.system_get_network_adapters() == ret


def test__system_get_network_adapter_device_functions():
    mock = MagicMock(
        return_value={
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/NetworkAdapters/NIC.Embedded.2/NetworkDeviceFunctions/NIC.Embedded.2-1-1"
                }
            ]
        }
    )

    adapter = "NIC.Embedded.2"
    ret = {
        "NIC.Embedded.2-1-1": {
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/NetworkAdapters/NIC.Embedded.2/NetworkDeviceFunctions/NIC.Embedded.2-1-1"
                }
            ]
        }
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.system_get_network_adapter_device_functions(adapter) == ret


def test__system_get_ethernet_devices():
    mock = MagicMock(
        return_value={
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/EthernetInterfaces/NIC.Embedded.2-1-1"
                }
            ]
        }
    )

    ret = {
        "NIC.Embedded.2-1-1": {
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Systems/System.Embedded.1/EthernetInterfaces/NIC.Embedded.2-1-1"
                }
            ]
        }
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.system_get_ethernet_devices() == ret


def test__get_firmware_inventory():
    mock = MagicMock(
        return_value={
            "Members": [
                {
                    "@odata.id": "/redfish/v1/UpdateService/FirmwareInventory/Current-101548-25.5.5.0005"
                }
            ]
        }
    )
    ret = {
        "Current-101548-25.5.5.0005": {
            "Members": [
                {
                    "@odata.id": "/redfish/v1/UpdateService/FirmwareInventory/Current-101548-25.5.5.0005"
                }
            ]
        }
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.get_firmware_inventory() == ret


def test__system_get_bios_attributes():
    mock = MagicMock(
        return_value={"Attributes": {"BootMode": "Uefi", "EmbSata": "AhciMode"}}
    )
    attribute_names = ["BootMode", "EmbSata"]
    ret = {"Attributes": {"BootMode": "Uefi", "EmbSata": "AhciMode"}}
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.system_get_bios_attributes(attribute_names) == ret


def test__get_system_info():
    mock = MagicMock(
        return_value={
            "@odata.context": "/redfish/v1/$metadata#ComputerSystem.ComputerSystem",
            "@odata.id": "/redfish/v1/Systems/System.Embedded.1",
            "@odata.type": "#ComputerSystem.v1_5_0.ComputerSystem",
            "Actions": {
                "#ComputerSystem.Reset": {
                    "ResetType@Redfish.AllowableValues": [
                        "On",
                        "ForceOff",
                        "ForceRestart",
                        "GracefulShutdown",
                        "PushPowerButton",
                        "Nmi",
                    ],
                    "target": "/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset",
                }
            },
        }
    )

    ret = {
        "@odata.context": "/redfish/v1/$metadata#ComputerSystem.ComputerSystem",
        "@odata.id": "/redfish/v1/Systems/System.Embedded.1",
        "@odata.type": "#ComputerSystem.v1_5_0.ComputerSystem",
        "Actions": {
            "#ComputerSystem.Reset": {
                "ResetType@Redfish.AllowableValues": [
                    "On",
                    "ForceOff",
                    "ForceRestart",
                    "GracefulShutdown",
                    "PushPowerButton",
                    "Nmi",
                ],
                "target": "/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset",
            }
        },
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.get_system_info() == ret


def test__system_get_boot_order():
    mock = MagicMock(
        return_value={
            "Boot": {
                "BootOrder": [
                    "Boot0000",
                    "Boot0007",
                    "Boot0009",
                    "Boot0002",
                    "Boot0005",
                    "Boot0006",
                    "Boot000A",
                ]
            }
        }
    )
    ret = [
        "Boot0000",
        "Boot0007",
        "Boot0009",
        "Boot0002",
        "Boot0005",
        "Boot0006",
        "Boot000A",
    ]
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.system_get_boot_order() == ret


def test__get_chassis_info():
    mock = MagicMock(
        return_value={
            "@odata.context": "/redfish/v1/$metadata#Chassis.Chassis",
            "@odata.id": "/redfish/v1/Chassis/System.Embedded.1",
            "@odata.type": "#Chassis.v1_6_0.Chassis",
            "Actions": {
                "#Chassis.Reset": {
                    "ResetType@Redfish.AllowableValues": ["On", "ForceOff"],
                    "target": "/redfish/v1/Chassis/System.Embedded.1/Actions/Chassis.Reset",
                }
            },
        }
    )

    ret = {
        "@odata.context": "/redfish/v1/$metadata#Chassis.Chassis",
        "@odata.id": "/redfish/v1/Chassis/System.Embedded.1",
        "@odata.type": "#Chassis.v1_6_0.Chassis",
        "Actions": {
            "#Chassis.Reset": {
                "ResetType@Redfish.AllowableValues": ["On", "ForceOff"],
                "target": "/redfish/v1/Chassis/System.Embedded.1/Actions/Chassis.Reset",
            }
        },
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.get_chassis_info() == ret


def test__chassis_get_assembly_info():
    mock = MagicMock(
        return_value={
            "Assemblies": [
                {
                    "@odata.context": "/redfish/v1/$metadata#Assembly.Assembly",
                    "@odata.etag": "1601983781",
                    "@odata.id": "/redfish/v1/Chassis/System.Embedded.1/Assembly/DIMM.Socket.A1",
                    "@odata.type": "#Assembly.v1_0_0.AssemblyData",
                    "BinaryDataURI": "null",
                    "Description": "DDR4 DIMM",
                    "EngineeringChangeLevel": "null",
                    "MemberId": "DIMM.Socket.A1",
                    "Model": "DDR4 DIMM",
                    "Name": "DIMM.Socket.A1#FRU",
                    "PartNumber": "M391A1K43BB2-CTD",
                    "Producer": "Samsung",
                    "ProductionDate": "2018-12-03T06:00:00Z",
                    "SKU": "null",
                    "SparePartNumber": "null",
                    "Vendor": "DELL",
                    "Version": "null",
                }
            ]
        }
    )

    ret = {
        "Assemblies": [
            {
                "@odata.context": "/redfish/v1/$metadata#Assembly.Assembly",
                "@odata.etag": "1601983781",
                "@odata.id": "/redfish/v1/Chassis/System.Embedded.1/Assembly/DIMM.Socket.A1",
                "@odata.type": "#Assembly.v1_0_0.AssemblyData",
                "BinaryDataURI": "null",
                "Description": "DDR4 DIMM",
                "EngineeringChangeLevel": "null",
                "MemberId": "DIMM.Socket.A1",
                "Model": "DDR4 DIMM",
                "Name": "DIMM.Socket.A1#FRU",
                "PartNumber": "M391A1K43BB2-CTD",
                "Producer": "Samsung",
                "ProductionDate": "2018-12-03T06:00:00Z",
                "SKU": "null",
                "SparePartNumber": "null",
                "Vendor": "DELL",
                "Version": "null",
            }
        ]
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.chassis_get_assembly_info() == ret


def test__chassis_get_cooled_by_info():
    mock = MagicMock(
        return_value={
            "Links": {
                "CooledBy": [
                    {
                        "@odata.id": "/redfish/v1/Chassis/System.Embedded.1/Sensors/Fans/0x17%7C%7CFan.Embedded.1"
                    }
                ]
            }
        }
    )
    ret = [
        {
            "@odata.id": "/redfish/v1/Chassis/System.Embedded.1/Sensors/Fans/0x17%7C%7CFan.Embedded.1"
        }
    ]
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.chassis_get_cooled_by_info() == ret


def test__chassis_get_powered_by_info():
    mock = MagicMock(
        return_value={
            "Links": {
                "PoweredBy": [
                    {
                        "@odata.id": "/redfish/v1/Chassis/System.Embedded.1/Power/PowerSupplies/PSU.Slot.1"
                    }
                ]
            }
        }
    )
    ret = [
        {
            "@odata.id": "/redfish/v1/Chassis/System.Embedded.1/Power/PowerSupplies/PSU.Slot.1"
        }
    ]
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.chassis_get_powered_by_info() == ret


def test__chassis_get_power_control_info():
    mock = MagicMock(
        return_value={
            "@odata.context": "/redfish/v1/$metadata#Power.Power",
            "@odata.id": "/redfish/v1/Chassis/System.Embedded.1/Power",
            "@odata.type": "#Power.v1_5_0.Power",
            "Description": "Power",
            "Id": "Power",
            "Name": "Power",
        }
    )
    ret = {
        "@odata.context": "/redfish/v1/$metadata#Power.Power",
        "@odata.id": "/redfish/v1/Chassis/System.Embedded.1/Power",
        "@odata.type": "#Power.v1_5_0.Power",
        "Description": "Power",
        "Id": "Power",
        "Name": "Power",
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.chassis_get_power_control_info() == ret


def test__chassis_get_power_consumed_watts():
    mock = MagicMock(return_value={"PowerControl": [{"PowerConsumedWatts": 50}]})
    ret = 50
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.chassis_get_power_consumed_watts() == ret


def test__manager_get_jobs():
    mock = MagicMock(
        return_value={
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/Oem/Dell/Jobs/JID_982691247371"
                }
            ]
        }
    )
    ret = {
        "Members": [
            {
                "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/Oem/Dell/Jobs/JID_982691247371"
            }
        ]
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.manager_get_jobs() == ret


def test__manager_get_job_detail():
    mock = MagicMock(
        return_value={
            "@odata.context": "/redfish/v1/$metadata#DellJob.DellJob",
            "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/Oem/Dell/Jobs/JID_982691247371",
            "@odata.type": "#DellJob.v1_1_0.DellJob",
            "ActualRunningStartTime": "null",
            "ActualRunningStopTime": "null",
            "CompletionTime": "2020-08-24T06:38:45",
            "Description": "Job Instance",
            "EndTime": "null",
            "Id": "JID_982691247371",
            "JobState": "Completed",
            "JobType": "iDRACConfiguration",
            "Message": "Job successfully Completed",
        }
    )
    ret = {
        "@odata.context": "/redfish/v1/$metadata#DellJob.DellJob",
        "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/Oem/Dell/Jobs/JID_982691247371",
        "@odata.type": "#DellJob.v1_1_0.DellJob",
        "ActualRunningStartTime": "null",
        "ActualRunningStopTime": "null",
        "CompletionTime": "2020-08-24T06:38:45",
        "Description": "Job Instance",
        "EndTime": "null",
        "Id": "JID_982691247371",
        "JobState": "Completed",
        "JobType": "iDRACConfiguration",
        "Message": "Job successfully Completed",
    }
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}):
        assert redfish.manager_get_job_detail(job_id="982691247371") == ret


def test__manager_delete_job_id():
    mock = MagicMock(return_value="123")
    ret = "123"
    with patch.dict(redfish.__proxy__, {"redfish.http_delete": mock}):
        assert redfish.manager_delete_job_id(job_id="982691247371") == ret


def test__manager_clear_jobs():
    mock1 = MagicMock(return_value="JID_758251537053")
    mock = MagicMock(
        return_value={
            "Id": "JobQueue",
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_758251537053"
                },
                {
                    "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_758452592711"
                },
                {
                    "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_759118382708"
                },
                {
                    "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_759310786751"
                },
                {
                    "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/JID_759981824121"
                },
            ],
        }
    )

    ret = {"result": True, "message": "Job queue is cleared successfully"}
    with patch.dict(redfish.__proxy__, {"redfish.http_get": mock}), patch.dict(
        redfish.__proxy__, {"redfish.http_delete": mock1}
    ):
        assert redfish.manager_clear_jobs() == ret
