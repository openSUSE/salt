# Author: Bo Maryniuk <bo@suse.de>


import os
import sys

import pytest
import salt.modules.ansiblegate as ansible
import salt.utils.path
import salt.utils.platform
import salt.config
import salt.loader
from salt.exceptions import LoaderError
from tests.support.mock import MagicMock, MockTimedProc, patch
from tests.support.runtests import RUNTIME_VARS

pytestmark = pytest.mark.skipif(
    salt.utils.platform.is_windows(), reason="Not supported on Windows"
)


@pytest.fixture
def configure_loader_modules():
    return {ansible: {"__utils__": {}}}


@pytest.fixture
def resolver():
    _resolver = ansible.AnsibleModuleResolver({})
    _resolver._modules_map = {
        "one.two.three": os.sep + os.path.join("one", "two", "three.py"),
        "four.five.six": os.sep + os.path.join("four", "five", "six.py"),
        "three.six.one": os.sep + os.path.join("three", "six", "one.py"),
    }
    return _resolver


def test_ansible_module_help(resolver):
    """
    Test help extraction from the module
    :return:
    """

    class Module:
        """
        An ansible module mock.
        """

        __name__ = "foo"
        DOCUMENTATION = """
---
one:
    text here
---
two:
    text here
description:
    describe the second part
    """

    with patch.object(ansible, "_resolver", resolver), patch.object(
        ansible._resolver, "load_module", MagicMock(return_value=Module())
    ):
        ret = ansible.help("dummy")
        assert sorted(
            ret.get('Available sections on module "{}"'.format(Module().__name__))
        ) == ["one", "two"]
        assert ret.get("Description") == "describe the second part"


def test_module_resolver_modlist(resolver):
    """
    Test Ansible resolver modules list.
    :return:
    """
    assert resolver.get_modules_list() == [
        "four.five.six",
        "one.two.three",
        "three.six.one",
    ]
    for ptr in ["five", "fi", "ve"]:
        assert resolver.get_modules_list(ptr) == ["four.five.six"]
    for ptr in ["si", "ix", "six"]:
        assert resolver.get_modules_list(ptr) == ["four.five.six", "three.six.one"]
    assert resolver.get_modules_list("one") == ["one.two.three", "three.six.one"]
    assert resolver.get_modules_list("one.two") == ["one.two.three"]
    assert resolver.get_modules_list("four") == ["four.five.six"]


def test_resolver_module_loader_failure(resolver):
    """
    Test Ansible module loader.
    :return:
    """
    mod = "four.five.six"
    with pytest.raises(ImportError) as import_error:
        resolver.load_module(mod)

    mod = "i.even.do.not.exist.at.all"
    with pytest.raises(LoaderError) as loader_error:
        resolver.load_module(mod)


def test_resolver_module_loader(resolver):
    """
    Test Ansible module loader.
    :return:
    """
    with patch("salt.modules.ansiblegate.importlib", MagicMock()), patch(
        "salt.modules.ansiblegate.importlib.import_module", lambda x: x
    ):
        assert resolver.load_module("four.five.six") == "ansible.modules.four.five.six"


def test_resolver_module_loader_import_failure(resolver):
    """
    Test Ansible module loader failure.
    :return:
    """
    with patch("salt.modules.ansiblegate.importlib", MagicMock()), patch(
        "salt.modules.ansiblegate.importlib.import_module", lambda x: x
    ):
        with pytest.raises(LoaderError) as loader_error:
            resolver.load_module("something.strange")


def test_virtual_function(resolver):
    """
    Test Ansible module __virtual__ when ansible is not installed on the minion.
    :return:
    """
    with patch("salt.modules.ansiblegate.ansible", None):
        assert ansible.__virtual__() == "ansible"


def test_ansible_module_call(resolver):
    """
    Test Ansible module call from ansible gate module
    :return:
    """

    class Module:
        """
        An ansible module mock.
        """

        __name__ = "one.two.three"
        __file__ = "foofile"

        def main():  # pylint: disable=no-method-argument
            pass

    ANSIBLE_MODULE_ARGS = '{"ANSIBLE_MODULE_ARGS": ["arg_1", {"kwarg1": "foobar"}]}'

    proc = MagicMock(
        side_effect=[
            MockTimedProc(stdout=ANSIBLE_MODULE_ARGS.encode(), stderr=None),
            MockTimedProc(stdout=b'{"completed": true}', stderr=None),
        ]
    )

    with patch.object(ansible, "_resolver", resolver), patch.object(
        ansible._resolver, "load_module", MagicMock(return_value=Module())
    ):
        _ansible_module_caller = ansible.AnsibleModuleCaller(ansible._resolver)
        with patch("salt.utils.timed_subprocess.TimedProc", proc):
            ret = _ansible_module_caller.call("one.two.three", "arg_1", kwarg1="foobar")
            proc.assert_any_call(
                [sys.executable, "foofile"],
                stdin=ANSIBLE_MODULE_ARGS,
                stdout=-1,
                timeout=1200,
            )
            try:
                proc.assert_any_call(
                    [
                        "echo",
                        '{"ANSIBLE_MODULE_ARGS": {"kwarg1": "foobar", "_raw_params": "arg_1"}}',
                    ],
                    stdout=-1,
                    timeout=1200,
                )
            except AssertionError:
                proc.assert_any_call(
                    [
                        "echo",
                        '{"ANSIBLE_MODULE_ARGS": {"_raw_params": "arg_1", "kwarg1": "foobar"}}',
                    ],
                    stdout=-1,
                    timeout=1200,
                )
            assert ret == {"completed": True, "timeout": 1200}


def test_ansible_playbooks_return_retcode(resolver):
    """
    Test ansible.playbooks execution module function include retcode in the return.
    :return:
    """
    ref_out = {"retcode": 0, "stdout": '{"foo": "bar"}'}
    cmd_run_all = MagicMock(return_value=ref_out)
    with patch.dict(ansible.__salt__, {"cmd.run_all": cmd_run_all}), patch(
        "salt.utils.path.which", MagicMock(return_value=True)
    ):
        ret = ansible.playbooks("fake-playbook.yml")
        assert "retcode" in ret


def test_ansible_targets():
    """
    Test ansible.targets execution module function.
    :return:
    """
    ansible_inventory_ret = """
{
    "_meta": {
        "hostvars": {
            "uyuni-stable-ansible-centos7-1.tf.local": {
                "ansible_ssh_private_key_file": "/etc/ansible/my_ansible_private_key"
            },
            "uyuni-stable-ansible-centos7-2.tf.local": {
                "ansible_ssh_private_key_file": "/etc/ansible/my_ansible_private_key"
            }
        }
    },
    "all": {
        "children": [
            "ungrouped"
        ]
    },
    "ungrouped": {
        "hosts": [
            "uyuni-stable-ansible-centos7-1.tf.local",
            "uyuni-stable-ansible-centos7-2.tf.local"
        ]
    }
}
    """
    ansible_inventory_mock = MagicMock(return_value=ansible_inventory_ret)
    with patch("salt.utils.path.which", MagicMock(return_value=True)):
        opts = salt.config.DEFAULT_MINION_OPTS.copy()
        utils = salt.loader.utils(opts, whitelist=["ansible"])
        with patch("salt.modules.cmdmod.run", ansible_inventory_mock), patch.dict(
            ansible.__utils__, utils), patch(
            "os.path.isfile", MagicMock(return_value=True)
        ):
            ret = ansible.targets()
            assert ansible_inventory_mock.call_args
            assert "_meta" in ret
            assert "uyuni-stable-ansible-centos7-1.tf.local" in ret["_meta"]["hostvars"]
            assert "ansible_ssh_private_key_file" in ret["_meta"]["hostvars"]["uyuni-stable-ansible-centos7-1.tf.local"]
            assert "all" in ret
            assert len(ret["ungrouped"]["hosts"]) == 2


def test_ansible_discover_playbooks_single_path():
    playbooks_dir = os.path.join(
        RUNTIME_VARS.TESTS_DIR, "unit/files/playbooks/example_playbooks/"
    )
    ret = ansible.discover_playbooks(playbooks_dir)
    assert playbooks_dir in ret
    assert ret[playbooks_dir]["playbook1.yml"] == {
        "fullpath": os.path.join(playbooks_dir, "playbook1.yml")
    }
    assert ret[playbooks_dir]["example-playbook2/site.yml"] == {
        "fullpath": os.path.join(playbooks_dir, "example-playbook2/site.yml"),
        "custom_inventory": os.path.join(playbooks_dir, "example-playbook2/hosts"),
    }


def test_ansible_discover_playbooks_single_path_using_parameters():
    playbooks_dir = os.path.join(
        RUNTIME_VARS.TESTS_DIR, "unit/files/playbooks/example_playbooks/"
    )
    ret = ansible.discover_playbooks(
        playbooks_dir, playbook_extension="foobar", hosts_filename="deadbeaf"
    )
    assert playbooks_dir in ret
    assert ret[playbooks_dir] == {}


def test_ansible_discover_playbooks_multiple_locations():
    playbooks_dir = os.path.join(
        RUNTIME_VARS.TESTS_DIR, "unit/files/playbooks/example_playbooks/"
    )
    ret = ansible.discover_playbooks(locations=[playbooks_dir, "/tmp/foobar"])
    assert playbooks_dir in ret
    assert "/tmp/foobar" in ret
    assert ret[playbooks_dir]["playbook1.yml"] == {
        "fullpath": os.path.join(playbooks_dir, "playbook1.yml")
    }
    assert ret[playbooks_dir]["example-playbook2/site.yml"] == {
        "fullpath": os.path.join(playbooks_dir, "example-playbook2/site.yml"),
        "custom_inventory": os.path.join(playbooks_dir, "example-playbook2/hosts"),
    }
