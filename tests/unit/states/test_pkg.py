# -*- coding: utf-8 -*-

# Import Python libs
from __future__ import absolute_import

# Import Salt Testing Libs
from tests.support.mixins import LoaderModuleMockMixin
from tests.support.unit import TestCase
from tests.support.mock import (
    MagicMock,
    patch)

# Import Salt Libs
from salt.ext import six
import salt.states.pkg as pkg
from salt.ext.six.moves import zip


class PkgTestCase(TestCase, LoaderModuleMockMixin):
    '''
    Test cases for salt.states.pkg
    '''
    pkgs = {
        'pkga': {'old': '1.0.1', 'new': '2.0.1'},
        'pkgb': {'old': '1.0.2', 'new': '2.0.2'},
        'pkgc': {'old': '1.0.3', 'new': '2.0.3'}
    }

    def setup_loader_modules(self):
        return {
            pkg: {
                '__grains__': {
                    'os': 'CentOS'
                }
            }
        }

    def test_uptodate_with_changes(self):
        '''
        Test pkg.uptodate with simulated changes
        '''
        list_upgrades = MagicMock(return_value={
            pkgname: pkgver['new'] for pkgname, pkgver in six.iteritems(self.pkgs)
        })
        upgrade = MagicMock(return_value=self.pkgs)
        version = MagicMock(side_effect=lambda pkgname, **_: self.pkgs[pkgname]['old'])

        with patch.dict(pkg.__salt__,
                        {'pkg.list_upgrades': list_upgrades,
                         'pkg.upgrade': upgrade,
                         'pkg.version': version}):

            # Run state with test=false
            with patch.dict(pkg.__opts__, {'test': False}):
                ret = pkg.uptodate('dummy', test=True)
                self.assertTrue(ret['result'])
                self.assertDictEqual(ret['changes'], self.pkgs)

            # Run state with test=true
            with patch.dict(pkg.__opts__, {'test': True}):
                ret = pkg.uptodate('dummy', test=True)
                self.assertIsNone(ret['result'])
                self.assertDictEqual(ret['changes'], self.pkgs)

    def test_uptodate_with_pkgs_with_changes(self):
        '''
        Test pkg.uptodate with simulated changes
        '''

        pkgs = {
            'pkga': {'old': '1.0.1', 'new': '2.0.1'},
            'pkgb': {'old': '1.0.2', 'new': '2.0.2'},
            'pkgc': {'old': '1.0.3', 'new': '2.0.3'}
        }

        list_upgrades = MagicMock(return_value={
            pkgname: pkgver['new'] for pkgname, pkgver in six.iteritems(self.pkgs)
        })
        upgrade = MagicMock(return_value=self.pkgs)
        version = MagicMock(side_effect=lambda pkgname, **_: pkgs[pkgname]['old'])

        with patch.dict(pkg.__salt__,
                        {'pkg.list_upgrades': list_upgrades,
                         'pkg.upgrade': upgrade,
                         'pkg.version': version}):
            # Run state with test=false
            with patch.dict(pkg.__opts__, {'test': False}):
                ret = pkg.uptodate('dummy', test=True, pkgs=[pkgname for pkgname in six.iterkeys(self.pkgs)])
                self.assertTrue(ret['result'])
                self.assertDictEqual(ret['changes'], pkgs)

            # Run state with test=true
            with patch.dict(pkg.__opts__, {'test': True}):
                ret = pkg.uptodate('dummy', test=True, pkgs=[pkgname for pkgname in six.iterkeys(self.pkgs)])
                self.assertIsNone(ret['result'])
                self.assertDictEqual(ret['changes'], pkgs)

    def test_uptodate_no_changes(self):
        '''
        Test pkg.uptodate with no changes
        '''
        list_upgrades = MagicMock(return_value={})
        upgrade = MagicMock(return_value={})

        with patch.dict(pkg.__salt__,
                        {'pkg.list_upgrades': list_upgrades,
                         'pkg.upgrade': upgrade}):

            # Run state with test=false
            with patch.dict(pkg.__opts__, {'test': False}):

                ret = pkg.uptodate('dummy', test=True)
                self.assertTrue(ret['result'])
                self.assertDictEqual(ret['changes'], {})

            # Run state with test=true
            with patch.dict(pkg.__opts__, {'test': True}):
                ret = pkg.uptodate('dummy', test=True)
                self.assertTrue(ret['result'])
                self.assertDictEqual(ret['changes'], {})

    def test_uptodate_with_pkgs_no_changes(self):
        '''
        Test pkg.uptodate with no changes
        '''
        list_upgrades = MagicMock(return_value={})
        upgrade = MagicMock(return_value={})

        with patch.dict(pkg.__salt__,
                        {'pkg.list_upgrades': list_upgrades,
                         'pkg.upgrade': upgrade}):
            # Run state with test=false
            with patch.dict(pkg.__opts__, {'test': False}):
                ret = pkg.uptodate('dummy', test=True, pkgs=[pkgname for pkgname in six.iterkeys(self.pkgs)])
                self.assertTrue(ret['result'])
                self.assertDictEqual(ret['changes'], {})

            # Run state with test=true
            with patch.dict(pkg.__opts__, {'test': True}):
                ret = pkg.uptodate('dummy', test=True, pkgs=[pkgname for pkgname in six.iterkeys(self.pkgs)])
                self.assertTrue(ret['result'])
                self.assertDictEqual(ret['changes'], {})

    def test_uptodate_with_failed_changes(self):
        '''
        Test pkg.uptodate with simulated failed changes
        '''

        pkgs = {
            'pkga': {'old': '1.0.1', 'new': '2.0.1'},
            'pkgb': {'old': '1.0.2', 'new': '2.0.2'},
            'pkgc': {'old': '1.0.3', 'new': '2.0.3'}
        }

        list_upgrades = MagicMock(return_value={
            pkgname: pkgver['new'] for pkgname, pkgver in six.iteritems(self.pkgs)
        })
        upgrade = MagicMock(return_value={})
        version = MagicMock(side_effect=lambda pkgname, **_: pkgs[pkgname]['old'])

        with patch.dict(pkg.__salt__,
                        {'pkg.list_upgrades': list_upgrades,
                         'pkg.upgrade': upgrade,
                         'pkg.version': version}):
            # Run state with test=false
            with patch.dict(pkg.__opts__, {'test': False}):
                ret = pkg.uptodate('dummy', test=True, pkgs=[pkgname for pkgname in six.iterkeys(self.pkgs)])
                self.assertFalse(ret['result'])
                self.assertDictEqual(ret['changes'], {})

            # Run state with test=true
            with patch.dict(pkg.__opts__, {'test': True}):
                ret = pkg.uptodate('dummy', test=True, pkgs=[pkgname for pkgname in six.iterkeys(self.pkgs)])
                self.assertIsNone(ret['result'])
                self.assertDictEqual(ret['changes'], pkgs)

    def test_parse_version_string(self):
        test_parameters = [
            ("> 1.0.0, < 15.0.0, != 14.0.1", [(">", "1.0.0"), ("<", "15.0.0"), ("!=", "14.0.1")]),
            ("> 1.0.0,< 15.0.0,!= 14.0.1", [(">", "1.0.0"), ("<", "15.0.0"), ("!=", "14.0.1")]),
            (">= 1.0.0, < 15.0.0", [(">=", "1.0.0"), ("<", "15.0.0")]),
            (">=1.0.0,< 15.0.0", [(">=", "1.0.0"), ("<", "15.0.0")]),
            ("< 15.0.0", [("<", "15.0.0")]),
            ("<15.0.0", [("<", "15.0.0")]),
            ("15.0.0", [("==", "15.0.0")]),
            ("", [])
        ]
        for version_string, expected_version_conditions in test_parameters:
            version_conditions = pkg._parse_version_string(version_string)
            self.assertEqual(len(expected_version_conditions),
                             len(version_conditions))
            for expected_version_condition, version_condition in zip(expected_version_conditions, version_conditions):
                self.assertEqual(
                    expected_version_condition[0], version_condition[0])
                self.assertEqual(
                    expected_version_condition[1], version_condition[1])

    def test_fulfills_version_string(self):
        test_parameters = [
            ("> 1.0.0, < 15.0.0, != 14.0.1", [], False),
            ("> 1.0.0, < 15.0.0, != 14.0.1", ["1.0.0"], False),
            ("> 1.0.0, < 15.0.0, != 14.0.1", ["14.0.1"], False),
            ("> 1.0.0, < 15.0.0, != 14.0.1", ["16.0.0"], False),
            ("> 1.0.0, < 15.0.0, != 14.0.1", ["2.0.0"], True),
            ("> 1.0.0, < 15.0.0, != 14.0.1", ["1.0.0", "14.0.1", "16.0.0", "2.0.0"], True),
            ("> 15.0.0", [], False),
            ("> 15.0.0", ["1.0.0"], False),
            ("> 15.0.0", ["16.0.0"], True),
            ("15.0.0", [], False),
            ("15.0.0", ["15.0.0"], True),
            # No version specified, whatever version installed. This is threated like ANY version installed fulfills.
            ("", ["15.0.0"], True),
            # No version specified, no version installed.
            ("", [], False)
        ]
        for version_string, installed_versions, expected_result in test_parameters:
            msg = "version_string: {}, installed_versions: {}, expected_result: {}".format(version_string, installed_versions, expected_result)
            self.assertEqual(expected_result, pkg._fulfills_version_string(installed_versions, version_string), msg)

    def test_fulfills_version_spec(self):
        test_parameters = [
            (["1.0.0", "14.0.1", "16.0.0", "2.0.0"], "==", "1.0.0", True),
            (["1.0.0", "14.0.1", "16.0.0", "2.0.0"], ">=", "1.0.0", True),
            (["1.0.0", "14.0.1", "16.0.0", "2.0.0"], ">", "1.0.0", True),
            (["1.0.0", "14.0.1", "16.0.0", "2.0.0"], "<", "2.0.0", True),
            (["1.0.0", "14.0.1", "16.0.0", "2.0.0"], "<=", "2.0.0", True),
            (["1.0.0", "14.0.1", "16.0.0", "2.0.0"], "!=", "1.0.0", True),
            (["1.0.0", "14.0.1", "16.0.0", "2.0.0"], "==", "17.0.0", False),
            (["1.0.0"], "!=", "1.0.0", False),
            ([], "==", "17.0.0", False),
        ]
        for installed_versions, operator, version, expected_result in test_parameters:
            msg = "installed_versions: {}, operator: {}, version: {}, expected_result: {}".format(installed_versions, operator, version, expected_result)
            self.assertEqual(expected_result, pkg._fulfills_version_spec(installed_versions, operator, version), msg)

    def test_held_unheld_Zypper(self):
        self.pkgr_held_unheld("Zypper")

    def test_held_unheld_YUM(self):
        self.pkgr_held_unheld("YUM/DNF")

    def test_held_unheld_APT(self):
        self.pkgr_held_unheld("APT")

    def pkgr_held_unheld(self, package_manager):
        """
        Test pkg.held and pkg.unheld with Zypper, YUM/DNF and APT
        """

        if package_manager == "Zypper":
            list_holds_func = "pkg.list_locks"
            list_holds_mock = MagicMock(
                return_value={
                    "bar": {
                        "type": "package",
                        "match_type": "glob",
                        "case_sensitive": "on",
                    },
                    "minimal_base": {
                        "type": "pattern",
                        "match_type": "glob",
                        "case_sensitive": "on",
                    },
                    "baz": {
                        "type": "package",
                        "match_type": "glob",
                        "case_sensitive": "on",
                    },
                }
            )
        elif package_manager == "YUM/DNF":
            list_holds_func = "pkg.list_holds"
            list_holds_mock = MagicMock(
                return_value=["bar-0:1.2.3-1.1.*", "baz-0:2.3.4-2.1.*"]
            )
        elif package_manager == "APT":
            list_holds_func = "pkg.get_selections"
            list_holds_mock = MagicMock(return_value={"hold": ["bar", "baz"]})

        def pkg_hold(name, pkgs=None, *_args, **__kwargs):
            if name and pkgs is None:
                pkgs = [name]
            ret = {}
            for pkg in pkgs:
                ret.update(
                    {
                        pkg: {
                            "name": pkg,
                            "changes": {"new": "hold", "old": ""},
                            "result": True,
                            "comment": "Package {} is now being held.".format(pkg),
                        }
                    }
                )
            return ret

        def pkg_unhold(name, pkgs=None, *_args, **__kwargs):
            if name and pkgs is None:
                pkgs = [name]
            ret = {}
            for pkg in pkgs:
                ret.update(
                    {
                        pkg: {
                            "name": pkg,
                            "changes": {"new": "", "old": "hold"},
                            "result": True,
                            "comment": "Package {} is no longer held.".format(pkg),
                        }
                    }
                )
            return ret
        hold_mock = MagicMock(side_effect=pkg_hold)
        unhold_mock = MagicMock(side_effect=pkg_unhold)

        # Testing with Zypper
        with patch.dict(
            pkg.__salt__,
            {
                list_holds_func: list_holds_mock,
                "pkg.hold": hold_mock,
                "pkg.unhold": unhold_mock,
            },
        ), patch.dict(
            pkg.__opts__, {
                "test": False,
            }
        ):
            # Holding one of two packages
            ret = pkg.held("held-test", pkgs=["foo", "bar"])
            assert "foo" in ret["changes"]
            assert len(ret["changes"]) == 1
            hold_mock.assert_called_once_with(name="held-test", pkgs=["foo"])
            unhold_mock.assert_not_called()

            hold_mock.reset_mock()
            unhold_mock.reset_mock()

            # Holding one of two packages and replacing all the rest held packages
            ret = pkg.held("held-test", pkgs=["foo", "bar"], replace=True)
            assert "foo" in ret["changes"]
            assert "baz" in ret["changes"]
            assert len(ret["changes"]) == 2
            hold_mock.assert_called_once_with(name="held-test", pkgs=["foo"])
            unhold_mock.assert_called_once_with(name="held-test", pkgs=["baz"])

            hold_mock.reset_mock()
            unhold_mock.reset_mock()

            # Remove all holds
            ret = pkg.held("held-test", pkgs=[], replace=True)
            assert "bar" in ret["changes"]
            assert "baz" in ret["changes"]
            assert len(ret["changes"]) == 2
            hold_mock.assert_not_called()
            unhold_mock.assert_any_call(name="held-test", pkgs=["baz"])
            unhold_mock.assert_any_call(name="held-test", pkgs=["bar"])

            hold_mock.reset_mock()
            unhold_mock.reset_mock()

            # Unolding one of two packages
            ret = pkg.unheld("held-test", pkgs=["foo", "bar"])
            assert "bar" in ret["changes"]
            assert len(ret["changes"]) == 1
            unhold_mock.assert_called_once_with(name="held-test", pkgs=["bar"])
            hold_mock.assert_not_called()

            hold_mock.reset_mock()
            unhold_mock.reset_mock()

            # Remove all holds
            ret = pkg.unheld("held-test", all=True)
            assert "bar" in ret["changes"]
            assert "baz" in ret["changes"]
            assert len(ret["changes"]) == 2
            hold_mock.assert_not_called()
            unhold_mock.assert_any_call(name="held-test", pkgs=["baz"])
            unhold_mock.assert_any_call(name="held-test", pkgs=["bar"])
