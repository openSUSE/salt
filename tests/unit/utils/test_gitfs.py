"""
These only test the provider selection and verification logic, they do not init
any remotes.
"""

import tempfile

import pytest
import tornado.ioloop

import salt.fileserver.gitfs
import salt.utils.files
import salt.utils.gitfs
import salt.utils.path
import salt.utils.platform
import tests.support.paths
from salt.exceptions import FileserverConfigError
from tests.support.helpers import patched_environ
from tests.support.mixins import AdaptedConfigurationTestCaseMixin
from tests.support.unit import TestCase


def _clear_instance_map():
    try:
        del salt.utils.gitfs.GitFS.instance_map[tornado.ioloop.IOLoop.current()]
    except KeyError:
        pass


class TestGitBase(TestCase, AdaptedConfigurationTestCaseMixin):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        tmp_name = self._tmp_dir.name

        class MockedProvider(
            salt.utils.gitfs.GitProvider
        ):  # pylint: disable=abstract-method
            def __init__(
                self,
                opts,
                remote,
                per_remote_defaults,
                per_remote_only,
                override_params,
                cache_root,
                role="gitfs",
            ):
                self.provider = "mocked"
                self.fetched = False
                super().__init__(
                    opts,
                    remote,
                    per_remote_defaults,
                    per_remote_only,
                    override_params,
                    cache_root,
                    role,
                )

            def init_remote(self):
                self.gitdir = salt.utils.path.join(tmp_name, ".git")
                self.repo = True
                new = False
                return new

            def envs(self):
                return ["base"]

            def fetch(self):
                self.fetched = True

        git_providers = {
            "mocked": MockedProvider,
        }
        gitfs_remotes = ["file://repo1.git", {"file://repo2.git": [{"name": "repo2"}]}]
        self.opts = self.get_temp_config(
            "master", gitfs_remotes=gitfs_remotes, verified_gitfs_provider="mocked"
        )
        self.main_class = salt.utils.gitfs.GitFS(
            self.opts,
            self.opts["gitfs_remotes"],
            per_remote_overrides=salt.fileserver.gitfs.PER_REMOTE_OVERRIDES,
            per_remote_only=salt.fileserver.gitfs.PER_REMOTE_ONLY,
            git_providers=git_providers,
        )

    @classmethod
    def setUpClass(cls):
        # Clear the instance map so that we make sure to create a new instance
        # for this test class.
        _clear_instance_map()

    def tearDown(self):
        # Providers are preserved with GitFS's instance_map
        for remote in self.main_class.remotes:
            remote.fetched = False
        del self.main_class
        self._tmp_dir.cleanup()

    def test_update_all(self):
        self.main_class.update()
        self.assertEqual(len(self.main_class.remotes), 2, "Wrong number of remotes")
        self.assertTrue(self.main_class.remotes[0].fetched)
        self.assertTrue(self.main_class.remotes[1].fetched)

    def test_update_by_name(self):
        self.main_class.update("repo2")
        self.assertEqual(len(self.main_class.remotes), 2, "Wrong number of remotes")
        self.assertFalse(self.main_class.remotes[0].fetched)
        self.assertTrue(self.main_class.remotes[1].fetched)

    def test_update_by_id_and_name(self):
        self.main_class.update([("file://repo1.git", None)])
        self.assertEqual(len(self.main_class.remotes), 2, "Wrong number of remotes")
        self.assertTrue(self.main_class.remotes[0].fetched)
        self.assertFalse(self.main_class.remotes[1].fetched)

    def test_get_cachedir_basename(self):
        self.assertEqual(
            self.main_class.remotes[0].get_cache_basename(),
            "_",
        )
        self.assertEqual(
            self.main_class.remotes[1].get_cache_basename(),
            "_",
        )

    def test_git_provider_mp_lock(self):
        """
        Check that lock is released after provider.lock()
        """
        provider = self.main_class.remotes[0]
        provider.lock()
        # check that lock has been released
        self.assertTrue(provider._master_lock.acquire(timeout=5))
        provider._master_lock.release()

    def test_git_provider_mp_clear_lock(self):
        """
        Check that lock is released after provider.clear_lock()
        """
        provider = self.main_class.remotes[0]
        provider.clear_lock()
        # check that lock has been released
        self.assertTrue(provider._master_lock.acquire(timeout=5))
        provider._master_lock.release()

    @pytest.mark.slow_test
    @pytest.mark.timeout_unless_on_windows(120)
    def test_git_provider_mp_lock_timeout(self):
        """
        Check that lock will time out if master lock is locked.
        """
        provider = self.main_class.remotes[0]
        # Hijack the lock so git provider is fooled into thinking another instance is doing somthing.
        self.assertTrue(provider._master_lock.acquire(timeout=5))
        try:
            # git provider should raise timeout error to avoid lock race conditions
            self.assertRaises(TimeoutError, provider.lock)
        finally:
            provider._master_lock.release()

    @pytest.mark.slow_test
    @pytest.mark.timeout_unless_on_windows(120)
    def test_git_provider_mp_clear_lock_timeout(self):
        """
        Check that clear lock will time out if master lock is locked.
        """
        provider = self.main_class.remotes[0]
        # Hijack the lock so git provider is fooled into thinking another instance is doing somthing.
        self.assertTrue(provider._master_lock.acquire(timeout=5))
        try:
            # git provider should raise timeout error to avoid lock race conditions
            self.assertRaises(TimeoutError, provider.clear_lock)
        finally:
            provider._master_lock.release()


@pytest.mark.skipif(not HAS_PYGIT2, reason="This host lacks proper pygit2 support")
@pytest.mark.skip_on_windows(
    reason="Skip Pygit2 on windows, due to pygit2 access error on windows"
)
class TestPygit2(TestCase):
    def _prepare_remote_repository(self, path):
        shutil.rmtree(path, ignore_errors=True)

        filecontent = "This is an empty README file"
        filename = "README"

        signature = pygit2.Signature(
            "Dummy Commiter", "dummy@dummy.com", int(time()), 0
        )

        repository = pygit2.init_repository(path, False)
        builder = repository.TreeBuilder()
        tree = builder.write()
        commit = repository.create_commit(
            "HEAD", signature, signature, "Create master branch", tree, []
        )
        repository.create_reference("refs/tags/simple_tag", commit)

        with salt.utils.files.fopen(
            os.path.join(repository.workdir, filename), "w"
        ) as file:
            file.write(filecontent)

        blob = repository.create_blob_fromworkdir(filename)
        builder = repository.TreeBuilder()
        builder.insert(filename, blob, pygit2.GIT_FILEMODE_BLOB)
        tree = builder.write()

        repository.index.read()
        repository.index.add(filename)
        repository.index.write()

        commit = repository.create_commit(
            "HEAD",
            signature,
            signature,
            "Added a README",
            tree,
            [repository.head.target],
        )
        repository.create_tag(
            "annotated_tag", commit, pygit2.GIT_OBJ_COMMIT, signature, "some message"
        )

    def _prepare_cache_repository(self, remote, cache):
        opts = {
            "cachedir": cache,
            "__role": "minion",
            "gitfs_disable_saltenv_mapping": False,
            "gitfs_base": "master",
            "gitfs_insecure_auth": False,
            "gitfs_mountpoint": "",
            "gitfs_passphrase": "",
            "gitfs_password": "",
            "gitfs_privkey": "",
            "gitfs_provider": "pygit2",
            "gitfs_pubkey": "",
            "gitfs_ref_types": ["branch", "tag", "sha"],
            "gitfs_refspecs": [
                "+refs/heads/*:refs/remotes/origin/*",
                "+refs/tags/*:refs/tags/*",
            ],
            "gitfs_root": "",
            "gitfs_saltenv_blacklist": [],
            "gitfs_saltenv_whitelist": [],
            "gitfs_ssl_verify": True,
            "gitfs_update_interval": 3,
            "gitfs_user": "",
            "verified_gitfs_provider": "pygit2",
        }
        per_remote_defaults = {
            "base": "master",
            "disable_saltenv_mapping": False,
            "insecure_auth": False,
            "ref_types": ["branch", "tag", "sha"],
            "passphrase": "",
            "mountpoint": "",
            "password": "",
            "privkey": "",
            "pubkey": "",
            "refspecs": [
                "+refs/heads/*:refs/remotes/origin/*",
                "+refs/tags/*:refs/tags/*",
            ],
            "root": "",
            "saltenv_blacklist": [],
            "saltenv_whitelist": [],
            "ssl_verify": True,
            "update_interval": 60,
            "user": "",
        }
        per_remote_only = ("all_saltenvs", "name", "saltenv")
        override_params = tuple(per_remote_defaults.keys())
        cache_root = os.path.join(cache, "gitfs")
        role = "gitfs"
        shutil.rmtree(cache_root, ignore_errors=True)
        provider = salt.utils.gitfs.Pygit2(
            opts,
            remote,
            per_remote_defaults,
            per_remote_only,
            override_params,
            cache_root,
            role,
        )
        return provider

    def test_checkout(self):
        remote = os.path.join(tests.support.paths.TMP, "pygit2-repo")
        cache = os.path.join(tests.support.paths.TMP, "pygit2-repo-cache")
        self._prepare_remote_repository(remote)
        provider = self._prepare_cache_repository(remote, cache)
        provider.remotecallbacks = None
        provider.credentials = None
        provider.init_remote()
        provider.fetch()
        provider.branch = "master"
        self.assertIn(provider.cachedir, provider.checkout())
        provider.branch = "simple_tag"
        self.assertIn(provider.cachedir, provider.checkout())
        provider.branch = "annotated_tag"
        self.assertIn(provider.cachedir, provider.checkout())
        provider.branch = "does_not_exist"
        self.assertIsNone(provider.checkout())

    def test_checkout_with_home_env_unset(self):
        remote = os.path.join(tests.support.paths.TMP, "pygit2-repo")
        cache = os.path.join(tests.support.paths.TMP, "pygit2-repo-cache")
        self._prepare_remote_repository(remote)
        provider = self._prepare_cache_repository(remote, cache)
        provider.remotecallbacks = None
        provider.credentials = None
        with patched_environ(__cleanup__=["HOME"]):
            self.assertTrue("HOME" not in os.environ)
            provider.init_remote()
            provider.fetch()
            self.assertTrue("HOME" in os.environ)
