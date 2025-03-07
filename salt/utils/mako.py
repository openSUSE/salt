"""
Functions for working with Mako templates
"""

try:
    # pylint: disable=import-error,3rd-party-module-not-gated,no-name-in-module
    from mako.lookup import TemplateCollection, TemplateLookup

    # pylint: enable=import-error,3rd-party-module-not-gated,no-name-in-module

    HAS_MAKO = True
except ImportError:
    HAS_MAKO = False

if HAS_MAKO:
    import os
    import urllib.parse

    import salt.fileclient
    import salt.utils.url

    class SaltMakoTemplateLookup(TemplateCollection):
        """
        Look up Mako template files using file:// or salt:// URLs with <%include/>
        or <%namespace/>.

        (1) Look up mako template files on local file system via files://... URL.
            Make sure mako template file is present locally on minion beforehand.

          Examples:
            <%include   file="file:///etc/salt/lib/templates/sls-parts.mako"/>
            <%namespace file="file:///etc/salt/lib/templates/utils.mako" import="helper"/>

        (2) Look up mako template files on Salt master via salt://... URL.
            If URL is a relative  path (without an URL scheme) then assume it's relative
            to the directory of the salt file that's doing the lookup. If URL is an absolute
            path then it's treated as if it has been prefixed with salt://.

           Examples::
             <%include   file="templates/sls-parts.mako"/>
             <%include   file="salt://lib/templates/sls-parts.mako"/>
             <%include   file="/lib/templates/sls-parts.mako"/>                 ##-- treated as salt://

             <%namespace file="templates/utils.mako"/>
             <%namespace file="salt://lib/templates/utils.mako" import="helper"/>
             <%namespace file="/lib/templates/utils.mako" import="helper"/>     ##-- treated as salt://

        """

        def __init__(self, opts, saltenv="base", pillar_rend=False):
            self.opts = opts
            self.saltenv = saltenv
            self._file_client = None
            self.pillar_rend = pillar_rend
            self.lookup = TemplateLookup(directories="/")
            self.cache = {}

        def file_client(self):
            """
            Setup and return file_client
            """
            if not self._file_client:
                self._file_client = salt.fileclient.get_file_client(
                    self.opts, self.pillar_rend
                )
            return self._file_client

        def adjust_uri(self, uri, filename):
            scheme = urllib.parse.urlparse(uri).scheme
            if scheme in ("salt", "file"):
                return uri
            elif scheme:
                raise ValueError("Unsupported URL scheme({}) in {}".format(scheme, uri))
            return self.lookup.adjust_uri(uri, filename)

        def get_template(self, uri, relativeto=None):
            if uri.startswith("file://"):
                proto = "file://"
                searchpath = "/"
                salt_uri = uri
            else:
                proto = "salt://"
                if self.opts["file_client"] == "local":
                    searchpath = self.opts["file_roots"][self.saltenv]
                else:
                    searchpath = [
                        os.path.join(self.opts["cachedir"], "files", self.saltenv)
                    ]
                salt_uri = uri if uri.startswith(proto) else salt.utils.url.create(uri)
                self.cache_file(salt_uri)

            self.lookup = TemplateLookup(directories=searchpath)
            return self.lookup.get_template(salt_uri[len(proto) :])

        def cache_file(self, fpath):
            if fpath not in self.cache:
                self.cache[fpath] = self.file_client().get_file(
                    fpath, "", True, self.saltenv
                )

        def destroy(self):
            if self._file_client:
                file_client = self._file_client
                self._file_client = None
                try:
                    file_client.destroy()
                except AttributeError:
                    pass
