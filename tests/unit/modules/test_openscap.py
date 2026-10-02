import subprocess

import salt.modules.openscap as openscap
from tests.support.mock import MagicMock, Mock, patch
from tests.support.unit import TestCase


class OpenscapTestCase(TestCase):

    random_temp_dir = "/tmp/unique-name"
    policy_file = "/usr/share/openscap/policy-file-xccdf.xml"

    def setUp(self):
        import salt.modules.openscap

        salt.modules.openscap.__salt__ = MagicMock()
        patchers = [
            patch("salt.modules.openscap.__salt__", MagicMock()),
            patch("salt.modules.openscap.shutil.rmtree", Mock()),
            patch(
                "salt.modules.openscap.tempfile.mkdtemp",
                Mock(return_value=self.random_temp_dir),
            ),
            patch("salt.modules.openscap.os.path.exists", Mock(return_value=True)),
        ]
        for patcher in patchers:
            self.apply_patch(patcher)

    def apply_patch(self, patcher):
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_openscap_xccdf_eval_success(self):
        with patch(
            "salt.modules.openscap.Popen",
            MagicMock(
                return_value=Mock(
                    **{"returncode": 0, "communicate.return_value": (bytes(0), bytes(0))}
                )
            ),
        ):
            response = openscap.xccdf(
                "eval --profile Default {}".format(self.policy_file)
            )

            self.assertEqual(openscap.tempfile.mkdtemp.call_count, 1)
            expected_cmd = [
                "oscap",
                "xccdf",
                "eval",
                "--oval-results",
                "--results",
                "results.xml",
                "--report",
                "report.html",
                "--profile",
                "Default",
                self.policy_file,
            ]
            openscap.Popen.assert_called_once_with(
                expected_cmd,
                cwd=openscap.tempfile.mkdtemp.return_value,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
            openscap.__salt__["cp.push_dir"].assert_called_once_with(
                self.random_temp_dir
            )
            self.assertEqual(openscap.shutil.rmtree.call_count, 1)
            self.assertEqual(
                response,
                {
                    "upload_dir": self.random_temp_dir,
                    "error": "",
                    "success": True,
                    "returncode": 0,
                },
            )

    def test_openscap_xccdf_eval_success_with_failing_rules(self):
        with patch(
            "salt.modules.openscap.Popen",
            MagicMock(
                return_value=Mock(
                    **{"returncode": 2, "communicate.return_value": (bytes(0), bytes("some error", "UTF-8"))}
                )
            ),
        ):
            response = openscap.xccdf(
                "eval --profile Default {}".format(self.policy_file)
            )

            self.assertEqual(openscap.tempfile.mkdtemp.call_count, 1)
            expected_cmd = [
                "oscap",
                "xccdf",
                "eval",
                "--oval-results",
                "--results",
                "results.xml",
                "--report",
                "report.html",
                "--profile",
                "Default",
                self.policy_file,
            ]
            openscap.Popen.assert_called_once_with(
                expected_cmd,
                cwd=openscap.tempfile.mkdtemp.return_value,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
            openscap.__salt__["cp.push_dir"].assert_called_once_with(
                self.random_temp_dir
            )
            self.assertEqual(openscap.shutil.rmtree.call_count, 1)
            self.assertEqual(
                response,
                {
                    "upload_dir": self.random_temp_dir,
                    "error": "some error",
                    "success": True,
                    "returncode": 2,
                },
            )

    def test_openscap_xccdf_eval_fail_no_profile(self):
        response = openscap.xccdf("eval --param Default /unknown/param")
        error = "the following arguments are required: --profile"
        self.assertEqual(
            response,
            {"error": error, "upload_dir": None, "success": False, "returncode": None},
        )

    def test_openscap_xccdf_eval_success_ignore_unknown_params(self):
        with patch(
            "salt.modules.openscap.Popen",
            MagicMock(
                return_value=Mock(
                    **{"returncode": 2, "communicate.return_value": (bytes(0), bytes("some error", "UTF-8"))}
                )
            ),
        ):
            response = openscap.xccdf(
                "eval --profile Default --param Default /policy/file"
            )
            self.assertEqual(
                response,
                {
                    "upload_dir": self.random_temp_dir,
                    "error": "some error",
                    "success": True,
                    "returncode": 2,
                },
            )
            expected_cmd = [
                "oscap",
                "xccdf",
                "eval",
                "--oval-results",
                "--results",
                "results.xml",
                "--report",
                "report.html",
                "--profile",
                "Default",
                "/policy/file",
            ]
            openscap.Popen.assert_called_once_with(
                expected_cmd,
                cwd=openscap.tempfile.mkdtemp.return_value,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )

    def test_openscap_xccdf_eval_evaluation_error(self):
        with patch(
            "salt.modules.openscap.Popen",
            MagicMock(
                return_value=Mock(
                    **{
                        "returncode": 1,
                        "communicate.return_value": (bytes(0), bytes("evaluation error", "UTF-8")),
                    }
                )
            ),
        ):
            response = openscap.xccdf(
                "eval --profile Default {}".format(self.policy_file)
            )

            self.assertEqual(
                response,
                {
                    "upload_dir": None,
                    "error": "evaluation error",
                    "success": False,
                    "returncode": 1,
                },
            )

    def test_openscap_xccdf_eval_fail_not_implemented_action(self):
        response = openscap.xccdf("info {}".format(self.policy_file))
        mock_err = "argument action: invalid choice: 'info' (choose from 'eval')"

        self.assertEqual(
            response,
            {
                "upload_dir": None,
                "error": mock_err,
                "success": False,
                "returncode": None,
            },
        )

    def test_new_openscap_xccdf_eval_success(self):
        with patch(
            "salt.modules.openscap.Popen",
            MagicMock(
                return_value=Mock(
                    **{"returncode": 0, "communicate.return_value": (bytes(0), bytes(0))}
                )
            ),
        ):
            response = openscap.xccdf_eval(
                self.policy_file,
                profile="Default",
                oval_results=True,
                results="results.xml",
                report="report.html",
            )

            self.assertEqual(openscap.tempfile.mkdtemp.call_count, 1)
            expected_cmd = [
                "oscap",
                "xccdf",
                "eval",
                "--oval-results",
                "--results",
                "results.xml",
                "--report",
                "report.html",
                "--profile",
                "Default",
                self.policy_file,
            ]
            openscap.Popen.assert_called_once_with(
                expected_cmd,
                cwd=openscap.tempfile.mkdtemp.return_value,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
            openscap.__salt__["cp.push_dir"].assert_called_once_with(
                self.random_temp_dir
            )
            self.assertEqual(openscap.shutil.rmtree.call_count, 1)
            self.assertEqual(
                response,
                {
                    "upload_dir": self.random_temp_dir,
                    "error": "",
                    "success": True,
                    "returncode": 0,
                },
            )

    def test_new_openscap_xccdf_eval_success_with_extra_ovalfiles(self):
        with patch(
            "salt.modules.openscap.Popen",
            MagicMock(
                return_value=Mock(
                    **{"returncode": 0, "communicate.return_value": (bytes(0), bytes(0))}
                )
            ),
        ):
            response = openscap.xccdf_eval(
                self.policy_file,
                ["/usr/share/xml/another-oval.xml", "/usr/share/xml/oval.xml"],
                profile="Default",
                oval_results=True,
                results="results.xml",
                report="report.html",
            )

            self.assertEqual(openscap.tempfile.mkdtemp.call_count, 1)
            expected_cmd = [
                "oscap",
                "xccdf",
                "eval",
                "--oval-results",
                "--results",
                "results.xml",
                "--report",
                "report.html",
                "--profile",
                "Default",
                self.policy_file,
                "/usr/share/xml/another-oval.xml",
                "/usr/share/xml/oval.xml",
            ]
            openscap.Popen.assert_called_once_with(
                expected_cmd,
                cwd=openscap.tempfile.mkdtemp.return_value,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
            openscap.__salt__["cp.push_dir"].assert_called_once_with(
                self.random_temp_dir
            )
            self.assertEqual(openscap.shutil.rmtree.call_count, 1)
            self.assertEqual(
                response,
                {
                    "upload_dir": self.random_temp_dir,
                    "error": "",
                    "success": True,
                    "returncode": 0,
                },
            )

    def test_new_openscap_xccdf_eval_success_with_failing_rules(self):
        with patch(
            "salt.modules.openscap.Popen",
            MagicMock(
                return_value=Mock(
                    **{"returncode": 2, "communicate.return_value": (bytes(0), bytes("some error", "UTF-8"))}
                )
            ),
        ):
            response = openscap.xccdf_eval(
                self.policy_file,
                profile="Default",
                oval_results=True,
                results="results.xml",
                report="report.html",
            )

            self.assertEqual(openscap.tempfile.mkdtemp.call_count, 1)
            expected_cmd = [
                "oscap",
                "xccdf",
                "eval",
                "--oval-results",
                "--results",
                "results.xml",
                "--report",
                "report.html",
                "--profile",
                "Default",
                self.policy_file,
            ]
            openscap.Popen.assert_called_once_with(
                expected_cmd,
                cwd=openscap.tempfile.mkdtemp.return_value,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
            openscap.__salt__["cp.push_dir"].assert_called_once_with(
                self.random_temp_dir
            )
            self.assertEqual(openscap.shutil.rmtree.call_count, 1)
            self.assertEqual(
                response,
                {
                    "upload_dir": self.random_temp_dir,
                    "error": "some error",
                    "success": True,
                    "returncode": 2,
                },
            )

    def test_new_openscap_xccdf_eval_success_ignore_unknown_params(self):
        with patch(
            "salt.modules.openscap.Popen",
            MagicMock(
                return_value=Mock(
                    **{"returncode": 2, "communicate.return_value": (bytes(0), bytes("some error", "UTF-8"))}
                )
            ),
        ):
            response = openscap.xccdf_eval(
                "/policy/file",
                param="Default",
                profile="Default",
                oval_results=True,
                results="results.xml",
                report="report.html",
            )

            self.assertEqual(
                response,
                {
                    "upload_dir": self.random_temp_dir,
                    "error": "some error",
                    "success": True,
                    "returncode": 2,
                },
            )
            expected_cmd = [
                "oscap",
                "xccdf",
                "eval",
                "--oval-results",
                "--results",
                "results.xml",
                "--report",
                "report.html",
                "--profile",
                "Default",
                "/policy/file",
            ]
            openscap.Popen.assert_called_once_with(
                expected_cmd,
                cwd=openscap.tempfile.mkdtemp.return_value,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )

    def test_new_openscap_xccdf_eval_evaluation_error(self):
        with patch(
            "salt.modules.openscap.Popen",
            MagicMock(
                return_value=Mock(
                    **{
                        "returncode": 1,
                        "communicate.return_value": (bytes(0), bytes("evaluation error", "UTF-8")),
                    }
                )
            ),
        ):
            response = openscap.xccdf_eval(
                self.policy_file,
                profile="Default",
                oval_results=True,
                results="results.xml",
                report="report.html",
            )

            self.assertEqual(
                response,
                {
                    "upload_dir": None,
                    "error": "evaluation error",
                    "success": False,
                    "returncode": 1,
                },
            )

    def test_new_openscap_xccdf_eval_success_with_skip_rules(self):
        with patch(
            "salt.modules.openscap.Popen",
            MagicMock(
                return_value=Mock(
                    **{
                        "returncode": 0,
                        "communicate.return_value": (bytes(0), bytes(0)),
                    }
                )
            ),
        ):
            response = openscap.xccdf_eval(
                self.policy_file,
                profile="Default",
                skip_rule=["rule-one", "rule-two"],
                oval_results=True,
                results="results.xml",
                report="report.html",
            )

            expected_cmd = [
                "oscap",
                "xccdf",
                "eval",
                "--oval-results",
                "--results",
                "results.xml",
                "--report",
                "report.html",
                "--profile",
                "Default",
                "--skip-rule",
                "rule-one",
                "--skip-rule",
                "rule-two",
                self.policy_file,
            ]
            openscap.Popen.assert_called_once_with(
                expected_cmd,
                cwd=openscap.tempfile.mkdtemp.return_value,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
            self.assertEqual(
                response,
                {
                    "upload_dir": self.random_temp_dir,
                    "error": "",
                    "success": True,
                    "returncode": 0,
                },
            )

    def test_new_openscap_xccdf_eval_success_with_single_rules_as_string(self):
        with patch(
            "salt.modules.openscap.Popen",
            MagicMock(
                return_value=Mock(
                    **{
                        "returncode": 0,
                        "communicate.return_value": (bytes(0), bytes(0)),
                    }
                )
            ),
        ):
            openscap.xccdf_eval(
                self.policy_file,
                profile="Default",
                rule="rule-one",
                skip_rule="rule-two",
                oval_results=True,
            )

            expected_cmd = [
                "oscap",
                "xccdf",
                "eval",
                "--oval-results",
                "--profile",
                "Default",
                "--rule",
                "rule-one",
                "--skip-rule",
                "rule-two",
                self.policy_file,
            ]
            openscap.Popen.assert_called_once_with(
                expected_cmd,
                cwd=openscap.tempfile.mkdtemp.return_value,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )

    def test_new_openscap_xccdf_eval_success_with_content_selection(self):
        with patch(
            "salt.modules.openscap.Popen",
            MagicMock(
                return_value=Mock(
                    **{
                        "returncode": 0,
                        "communicate.return_value": (bytes(0), bytes(0)),
                    }
                )
            ),
        ):
            openscap.xccdf_eval(
                self.policy_file,
                profile="Default",
                reference="stigid:RHEL-09-211010",
                cpe="/usr/share/openscap/cpe/openscap-cpe-dict.xml",
                datastream_id="scap_org.open-scap_datastream_from_xccdf",
                xccdf_id="scap_org.open-scap_cref_xccdf.xml",
                benchmark_id="xccdf_org.ssgproject.content_benchmark_RHEL-9",
                local_files="/var/cache/openscap",
                fetch_remote_resources=True,
            )

            expected_cmd = [
                "oscap",
                "xccdf",
                "eval",
                "--profile",
                "Default",
                "--reference",
                "stigid:RHEL-09-211010",
                "--cpe",
                "/usr/share/openscap/cpe/openscap-cpe-dict.xml",
                "--datastream-id",
                "scap_org.open-scap_datastream_from_xccdf",
                "--xccdf-id",
                "scap_org.open-scap_cref_xccdf.xml",
                "--benchmark-id",
                "xccdf_org.ssgproject.content_benchmark_RHEL-9",
                "--fetch-remote-resources",
                "--local-files",
                "/var/cache/openscap",
                self.policy_file,
            ]
            openscap.Popen.assert_called_once_with(
                expected_cmd,
                cwd=openscap.tempfile.mkdtemp.return_value,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
