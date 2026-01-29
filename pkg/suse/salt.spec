#
# spec file for package salt
#
# Copyright (c) 2024 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#


%global debug_package %{nil}

%if 0%{?suse_version} > 1500
%bcond_without libalternatives
%else
%bcond_with libalternatives
%endif
%if 0%{?sle_version} >= 150400 || 0%{?suse_version} >= 1600
%define _alternatives 1
%endif

%global flavor @BUILD_FLAVOR@%{nil}
%if "%{flavor}" == "testsuite"
%define psuffix -test
%else
%define psuffix %{nil}
%endif

%if 0%{?suse_version} > 1210 || 0%{?rhel} >= 7 || 0%{?fedora} >= 28
%bcond_without systemd
%else
%bcond_with    systemd
%endif
%if 0%{?suse_version} > 1110
%bcond_without bash_completion
%bcond_without fish_completion
%bcond_without zsh_completion
%else
%bcond_with    bash_completion
%bcond_with    fish_completion
%bcond_with    zsh_completion
%endif
%bcond_without docs
%bcond_with    builddocs

%if %{without systemd}
%define service_del_preun echo %{*}
%endif
%if 0%{?sle_version} >= 150700
%{?sle15_python_module_pythons}
%else
%{?sle15allpythons}
%endif
%define skip_python2 1
%if 0%{?rhel} == 8 || (0%{?suse_version} == 1500 && 0%{?sle_version} < 150400)
%define singlespec_compat 1
%define __python3_bin_suffix 3.6
%if 0%{?rhel} == 8
%define __python3 /usr/libexec/platform-python
%else
%define __python3 /usr/bin/python3
%endif
%define python_module() python3-%**
%define python_files() -n python3-%1
%define python_subpackages %{nil}
%define python_sitelib %python3_sitelib
%define python_expand(+abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-=) %{lua: \
local args = rpm.expand("%**")\
local python_bin = rpm.expand("%__python3")\
local python_bin_suffix = rpm.expand("%__python3_bin_suffix")\
args = args:gsub("$python_bin_suffix", python_bin_suffix)\
args = args:gsub("$python_sitelib", "python3_sitelib")\
args = args:gsub("$python", python_bin)\
print(rpm.expand(args .. "\\n"))\
}
%endif
Name:           salt%{psuffix}
Version:        3006.0
Release:        0
Summary:        A parallel remote execution system
License:        Apache-2.0
Group:          System/Management
URL:            https://saltproject.io/
#!CreateArchive: salt
Source:         salt-%{version}.tar.gz
Source1:        README.SUSE
Source2:        salt-tmpfiles.d
Source3:        html.tar.bz2
Source4:        update-documentation.sh
Source6:        transactional_update.conf





# (closed upstream in favor of different solution - might affect server_id)





# (master PR not yet created - codejam)
#                     https://github.com/saltstack/salt/commit/e20362f6f053eaa4144583604e6aac3d62838419
# Can be dropped one pull/50453 is in released version.






# (deviation from upstream - we should probably port this)




# (revert https://github.com/saltstack/salt/pull/58655)










# Fix problem caused by: https://github.com/openSUSE/salt/pull/493 (Patch47) affecting only 3005.1.



BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildRequires:  logrotate
%if 0%{?suse_version} > 1020
BuildRequires:  fdupes
%endif

%if 0%{?_alternatives}
Requires:       %{name}-call = %{version}-%{release}
%else
Requires:       python3-%{name} = %{version}-%{release}
%endif
Obsoletes:      python2-%{name}

# The "salt" package obsoletes "python3-salt" in SLE15SP7+
%if 0%{?sle_version} >= 150700
Obsoletes:      python3-%{name}
%endif

Requires(pre):  %{_sbindir}/groupadd
Requires(pre):  %{_sbindir}/useradd
Provides:       user(salt)
Provides:       group(salt)

%if 0%{?suse_version}
Requires(pre):  shadow
%endif

%if 0%{?suse_version}
Requires(pre):  dbus-1
%else
Requires(pre):  dbus
%endif

Requires:       logrotate
Requires:       procps

%if 0%{?suse_version} >= 1500
Requires:       iproute2
%else
%if 0%{?suse_version}
Requires:       net-tools
%else
Requires:       iproute
%endif
%endif

%if %{with systemd}
BuildRequires:  pkgconfig(systemd)
%{?systemd_ordering}
%endif

%if %{with fish_completion}
%define fish_dir %{_datadir}/fish/
%define fish_completions_dir %{_datadir}/fish/completions/
%endif

%if %{with bash_completion}
%if 0%{?suse_version} >= 1140
BuildRequires:  bash-completion
%else
BuildRequires:  bash
%endif
%endif

%if %{with zsh_completion}
BuildRequires:  zsh
%endif

%define python_subpackage_only 1
%python_subpackages

%description
Salt is a distributed remote execution system used to execute commands and
query data. It was developed in order to bring the best solutions found in
the world of remote execution together and make them better, faster and more
malleable. Salt accomplishes this via its ability to handle larger loads of
information, and not just dozens, but hundreds or even thousands of individual
servers, handle them quickly and through a simple and manageable interface.

%if "%{flavor}" != "testsuite"

%if 0%{?singlespec_compat}
%package -n python3-salt
%else
%package -n python-salt
%endif
Summary:        python3 library for salt
Group:          System/Management
Requires:       %{name} = %{version}-%{release}
BuildRequires:  python-rpm-macros
%if 0%{?rhel} == 8
BuildRequires:  platform-python
%else
BuildRequires:  %{python_module base}
%endif
BuildRequires:  %{python_module setuptools}
# requirements/base.txt
%if 0%{?rhel} || 0%{?fedora}
BuildRequires:  python3-jinja2
BuildRequires:  python3-m2crypto
BuildRequires:  python3-markupsafe
BuildRequires:  python3-msgpack > 0.3
BuildRequires:  python3-zmq >= 2.2.0
%else
BuildRequires:  %{python_module Jinja2}
BuildRequires:  %{python_module MarkupSafe}
BuildRequires:  %{python_module msgpack-python > 0.3}
BuildRequires:  %{python_module pyzmq > 2.2.0}
%if 0%{?suse_version} >= 1500
BuildRequires:  %{python_module M2Crypto}
%else
BuildRequires:  %{python_module pycrypto >= 2.6.1}
%endif
%endif
BuildRequires:  %{python_module PyYAML}
BuildRequires:  %{python_module psutil}
BuildRequires:  %{python_module requests >= 1.0.0}
BuildRequires:  %{python_module distro}
BuildRequires:  %{python_module looseversion}
BuildRequires:  %{python_module packaging}
BuildRequires:  %{python_module contextvars}

# requirements/zeromq.txt
%if %{with test}
BuildRequires:  %{python_module boto >= 2.32.1}
BuildRequires:  %{python_module mock if %python-base < 3.8}
BuildRequires:  %{python_module moto >= 0.3.6}
BuildRequires:  %{python_module pip}
BuildRequires:  %{python_module salt-testing >= 2015.2.16}
BuildRequires:  %{python_module unittest2}
BuildRequires:  %{python_module xml}
%endif
%if %{with builddocs}
BuildRequires:  %{python_module sphinx}
%endif
%if 0%{?rhel} == 8
Requires:       platform-python
%else
%if 0%{?singlespec_compat}
Requires:       %{python_module base}
%else
Requires:       python-base
%endif
%endif

%if 0%{?_alternatives}
%if %{with libalternatives}
Requires:       alts
BuildRequires:  alts
%else
Requires(post): update-alternatives
Requires(postun):update-alternatives
%endif
%endif

# requirements/base.txt
%if 0%{?rhel} || 0%{?fedora}
Requires:       python3-jinja2
Requires:       python3-m2crypto
Requires:       python3-markupsafe
Requires:       python3-msgpack > 0.3
Requires:       python3-zmq >= 2.2.0

%if 0%{?rhel} >= 8 || 0%{?fedora} >= 30
Requires:       dnf
Requires:       python3-dnf-plugins-core
%endif
%else # SUSE
%if 0%{?singlespec_compat}
Requires:       %{python_module Jinja2}
Requires:       %{python_module MarkupSafe}
Requires:       %{python_module msgpack-python > 0.3}
%if 0%{?suse_version} >= 1500
Requires:       %{python_module M2Crypto}
%else
Requires:       %{python_module pycrypto >= 2.6.1}
%endif
Requires:       %{python_module pyzmq >= 2.2.0}
%else
Requires:       python-Jinja2
Requires:       python-MarkupSafe
Requires:       python-msgpack-python > 0.3
%if 0%{?suse_version} >= 1500
Requires:       python-M2Crypto
%else
Requires:       python-pycrypto >= 2.6.1
%endif
Requires:       python-pyzmq >= 2.2.0
%endif
%endif # end of RHEL / SUSE specific section
%if 0%{?singlespec_compat}
Recommends:     %{python_module jmespath}
Requires:       %{python_module PyYAML}
Requires:       %{python_module psutil}
Requires:       %{python_module requests >= 1.0.0}
Requires:       %{python_module distro}
Requires:       %{python_module looseversion}
Requires:       %{python_module packaging}
Requires:       %{python_module contextvars}
Requires:       %{python_module cryptography}
%if 0%{?suse_version}
# required for zypper.py
Requires:       %{python_module rpm}
# requirements/opt.txt (not all)
# Suggests:     python-MySQL-python  ## Disabled for now, originally Recommended
Suggests:       %{python_module timelib}
Suggests:       %{python_module gnupg}
%endif
%else
Recommends:     python-jmespath
Requires:       python-PyYAML
Requires:       python-psutil
Requires:       python-requests >= 1.0.0
Requires:       python-distro
Requires:       python-looseversion
Requires:       python-packaging
Requires:       python-contextvars
Requires:       python-cryptography
%if 0%{?suse_version}
# required for zypper.py
Requires:       python-rpm
# requirements/opt.txt (not all)
# Suggests:     python-MySQL-python  ## Disabled for now, originally Recommended
Suggests:       python-timelib
Suggests:       python-gnupg
# requirements/zeromq.txt
%endif
%endif
#
%if 0%{?suse_version}
# python-xml is part of python-base in all rhel versions
%if 0%{?singlespec_compat}
Requires:       %{python_module xml}
Requires:       %{python_module zypp-plugin}
Suggests:       %{python_module Mako}
Recommends:     %{python_module netaddr}
Recommends:     %{python_module pyinotify}
%else
Requires:       python-xml
Requires:       python-zypp-plugin
Suggests:       python-Mako
Recommends:     python-netaddr
Recommends:     python-pyinotify
%endif
Requires(pre):  libzypp(plugin:system) >= 0
%endif

# Required by Salt modules
Requires:       iputils
Requires:       sudo
Requires:       file
Recommends:     man
%if 0%{?singlespec_compat}
Recommends:     %{python_module passlib}
%else
Recommends:     python-passlib
%endif

%if 0%{?suse_version} >= 1600
Requires:       python-tornado
%if 0%{?python3_version_nodots} > 312
Requires:       python-legacy-cgi
%endif
%else
%if 0%{?singlespec_compat}
Provides:       bundled(%{python_module tornado}) = 4.5.3
%else
Provides:       bundled(python-tornado) = 4.5.3
%endif
%endif

Provides:       %{name}-call = %{version}-%{release}

%if 0%{?singlespec_compat}
%description -n python3-salt
%else
%description -n python-salt
%endif
Python3 specific files for salt

%package api
Summary:        The api for Salt a parallel remote execution system
Group:          System/Management
Requires:       %{name} = %{version}-%{release}
Requires:       %{name}-master = %{version}-%{release}
%if 0%{?suse_version}
%if 0%{?sle_version} >= 150400
Requires:       %{python_module CherryPy >= 3.2.2 if %python-salt}
%else
Requires:       python3-CherryPy >= 3.2.2
%endif
%else
Requires:       python3-cherrypy >= 3.2.2
%endif

%description api
salt-api is a modular interface on top of Salt that can provide a variety of entry points into a running Salt system.

%package cloud
Summary:        Generic cloud provisioning tool for Saltstack
Group:          System/Management
Requires:       %{name} = %{version}-%{release}
Requires:       %{name}-master = %{version}-%{release}
%if 0%{?suse_version}
%if 0%{?sle_version} >= 150400
Requires:       %{python_module apache-libcloud if %python-salt}
Recommends:     %{python_module botocore if %python-salt}
Recommends:     %{python_module netaddr if %python-salt}
%else
Requires:       python3-apache-libcloud
Recommends:     python3-botocore
Recommends:     python3-netaddr
%endif
%else
Requires:       python3-apache-libcloud
%endif

%description cloud
public cloud VM management system
provision virtual machines on various public clouds via a cleanly
controlled profile and mapping system.

%if %{with docs}
%package doc
Summary:        Documentation for salt, a parallel remote execution system
Group:          Documentation/HTML
Requires:       %{name} = %{version}

%description doc
This contains the documentation of salt, it is an offline version of http://docs.saltstack.com.
%endif

%package master
Summary:        The management component of Saltstack with zmq protocol supported
Group:          System/Management
Requires:       %{name} = %{version}-%{release}
%if 0%{?suse_version}
%if 0%{?sle_version} >= 150400
Recommends:     %{python_module pygit2 >= 0.20.3 if %python-salt}
%else
Recommends:     python3-pygit2 >= 0.20.3
%endif
%endif
%ifarch %{ix86} x86_64
%if 0%{?suse_version}
%if 0%{?suse_version} > 1110
Requires:       dmidecode
%else
Requires:       pmtools
%endif
%endif
%endif
%if %{with systemd}
%{?systemd_requires}
BuildRequires:  systemd
%endif

%description master
The Salt master is the central server to which all minions connect.
Enabled commands to remote systems to be called in parallel rather
than serially.

%package minion
Summary:        The client component for Saltstack
Group:          System/Management
Requires:       %{name} = %{version}-%{release}
%if 0%{?suse_version} > 1500 || 0%{?sle_version} > 150000
Requires:       (%{name}-transactional-update = %{version}-%{release} if read-only-root-fs)
%endif

%if %{with systemd}
%{?systemd_requires}
%endif

%description minion
Salt minion is queried and controlled from the master.
Listens to the salt master and execute the commands.

%package proxy
Summary:        Component for salt that enables controlling arbitrary devices
Group:          System/Management
Requires:       %{name} = %{version}-%{release}
%if %{with systemd}
%{?systemd_requires}
%endif

%description proxy
Proxy minions are a developing Salt feature that enables controlling devices that,
for whatever reason, cannot run a standard salt-minion.
Examples include network gear that has an API but runs a proprietary OS,
devices with limited CPU or memory, or devices that could run a minion, but for
security reasons, will not.

%package syndic
Summary:        The syndic component for saltstack
Group:          System/Management
Requires:       %{name} = %{version}-%{release}
Requires:       %{name}-master = %{version}-%{release}
%if %{with systemd}
%{?systemd_requires}
%endif

%description syndic
Salt syndic is the master-of-masters for salt
The master of masters for salt-- it enables
the management of multiple masters at a time..

%package ssh
Summary:        Management component for Saltstack with ssh protocol
Group:          System/Management
Requires:       %{name} = %{version}-%{release}
Requires:       %{name}-master = %{version}-%{release}
%if 0%{?suse_version}
Recommends:     sshpass
%endif
%if %{with systemd}
%{?systemd_requires}
%endif

%description ssh
Salt ssh is a master running without zmq.
it enables the management of minions over a ssh connection.

%if %{with bash_completion}
%package bash-completion
Summary:        Bash Completion for %{name}
Group:          System/Management
Requires:       %{name} = %{version}-%{release}
Requires:       bash-completion
%if 0%{?suse_version} > 1110
BuildArch:      noarch
%endif

%description bash-completion
Bash command line completion support for %{name}.

%endif

%if %{with fish_completion}
%package fish-completion
Summary:        Fish Completion for %{name}
Group:          System/Management
Requires:       %{name} = %{version}-%{release}

%if 0%{?suse_version} > 1110
BuildArch:      noarch
%endif

%description fish-completion
Fish command line completion support for %{name}.
%endif

%if %{with zsh_completion}
%package zsh-completion
Summary:        Zsh Completion for %{name}
Group:          System/Management
Requires:       %{name} = %{version}-%{release}
Requires:       zsh
%if 0%{?suse_version} > 1110
BuildArch:      noarch
%endif

%description zsh-completion
Zsh command line completion support for %{name}.

%endif

%package standalone-formulas-configuration
Summary:        Standalone Salt configuration to make the packaged formulas available for the Salt master
Group:          System/Management
Requires:       %{name}
Provides:       salt-formulas-configuration
Conflicts:      otherproviders(salt-formulas-configuration)

%description standalone-formulas-configuration
This package adds the standalone configuration for the Salt master in order to make the packaged Salt formulas available on the Salt master

%package transactional-update
Summary:        Transactional update executor configuration
Group:          System/Management
Requires:       %{name} = %{version}-%{release}
Requires:       %{name}-minion = %{version}-%{release}
Requires:       tar

%description transactional-update
For transactional systems, like MicroOS, Salt can operate
transparently if the executor "transactional-update" is registered in
list of active executors.  This package add the configuration file.

%endif

%if "%{flavor}" == "testsuite"

%if 0%{?singlespec_compat}
%package -n python3-salt-testsuite
%else
%package -n python-salt-testsuite
%endif
Summary:        Unit and integration tests for Salt

%if 0%{?rhel} == 8
BuildRequires:  platform-python
%else
BuildRequires:  %{python_module base}
%endif
BuildRequires:  %{python_module setuptools}

Requires:       salt = %{version}
%if 0%{?singlespec_compat}
Requires:       %{python_module CherryPy}
Requires:       %{python_module Genshi}
Requires:       %{python_module Mako}
%if !0%{?suse_version} > 1600 || 0%{?centos}
Requires:       %{python_module boto}
%endif
Requires:       %{python_module boto3}
Requires:       %{python_module docker}
%if 0%{?suse_version} < 1600
Requires:       %{python_module mock}
%endif
Requires:       %{python_module pygit2}
Requires:       %{python_module pytest >= 7.0.1}
Requires:       %{python_module pytest-httpserver}
Requires:       %{python_module pytest-salt-factories >= 1.0.0~rc21}
Requires:       %{python_module pytest-subtests}
Requires:       %{python_module testinfra}
Requires:       %{python_module yamllint}
Requires:       %{python_module pip}
%else
Requires:       python-CherryPy
Requires:       python-Genshi
Requires:       python-Mako
%if !0%{?suse_version} > 1600 || 0%{?centos}
Requires:       python-boto
%endif
Requires:       python-boto3
Requires:       python-docker
%if 0%{?suse_version} < 1600
Requires:       python-mock
%endif
Requires:       python-pygit2
Requires:       python-pytest >= 7.0.1
Requires:       python-pytest-httpserver
Requires:       python-pytest-salt-factories >= 1.0.0~rc21
Requires:       python-pytest-subtests
Requires:       python-testinfra
Requires:       python-yamllint
Requires:       python-pip
%endif
Requires:       docker
Requires:       openssh
Requires:       git

Obsoletes:      %{name}-tests

%if 0%{?singlespec_compat}
%description -n python3-salt-testsuite
%else
%description -n python-salt-testsuite
%endif
Collection of unit, functional, and integration tests for %{name}.

%endif

%prep
%setup -q
cp %{S:1} .
cp %{S:6} .

%build
%if "%{flavor}" != "testsuite"

# Putting /usr/bin at the front of $PATH is needed for RHEL/RES 7. Without this
# change, the RPM will require /bin/python, which is not provided by any package
# on RHEL/RES 7.
%if 0%{?fedora} || 0%{?rhel}
export PATH=/usr/bin:$PATH
%endif
%{python_expand #
$python setup.py --with-salt-version=%{version} --salt-transport=both build
mv build _build.%{$python_bin_suffix}
}

%if %{with docs} && %{without builddocs}
# extract docs from the tarball
mkdir -p doc/_build
pushd doc/_build/
tar xfv %{S:3}
popd
%endif

%if %{with docs} && %{with builddocs}
## documentation
cd doc && make html && rm _build/html/.buildinfo && rm _build/html/_images/proxy_minions.png && cd _build/html && chmod -R -x+X *
%endif

%endif

%install
%if "%{flavor}" != "testsuite"

%{python_expand #
mv _build.%{$python_bin_suffix} build
$python setup.py --salt-transport=both install --prefix=%{_prefix} --root=%{buildroot}
mv build _build.%{$python_bin_suffix}

DEF_PYPATH=_build.%{$python_bin_suffix}/scripts-*/

rm -f %{buildroot}%{_bindir}/*
for script in $DEF_PYPATH/*; do
  install -m 0755 $script %{buildroot}%{_bindir}
done
}

## create missing directories
install -Dd -m 0750 %{buildroot}%{_localstatedir}/cache/salt/cloud
install -Dd -m 0750 %{buildroot}%{_localstatedir}/cache/salt/master
install -Dd -m 0750 %{buildroot}%{_localstatedir}/cache/salt/master/jobs
install -Dd -m 0750 %{buildroot}%{_localstatedir}/cache/salt/master/proc
install -Dd -m 0750 %{buildroot}%{_localstatedir}/cache/salt/master/queues
install -Dd -m 0750 %{buildroot}%{_localstatedir}/cache/salt/master/roots
install -Dd -m 0750 %{buildroot}%{_localstatedir}/cache/salt/master/syndics
install -Dd -m 0750 %{buildroot}%{_localstatedir}/cache/salt/master/tokens
install -Dd -m 0750 %{buildroot}%{_localstatedir}/cache/salt/minion/extmod
install -Dd -m 0750 %{buildroot}%{_localstatedir}/log/salt
install -Dd -m 0750 %{buildroot}%{_sysconfdir}/salt/
install -Dd -m 0750 %{buildroot}%{_sysconfdir}/salt/cloud.maps.d
install -Dd -m 0750 %{buildroot}%{_sysconfdir}/salt/cloud.profiles.d
install -Dd -m 0750 %{buildroot}%{_sysconfdir}/salt/cloud.providers.d
install -Dd -m 0750 %{buildroot}%{_sysconfdir}/salt/master.d
install -Dd -m 0750 %{buildroot}%{_sysconfdir}/salt/minion.d
install -Dd -m 0750 %{buildroot}%{_sysconfdir}/salt/pki
install -Dd -m 0750 %{buildroot}%{_sysconfdir}/salt/pki/master
install -Dd -m 0750 %{buildroot}%{_sysconfdir}/salt/pki/master/minions
install -Dd -m 0750 %{buildroot}%{_sysconfdir}/salt/pki/master/minions_autosign
install -Dd -m 0750 %{buildroot}%{_sysconfdir}/salt/pki/master/minions_denied
install -Dd -m 0750 %{buildroot}%{_sysconfdir}/salt/pki/master/minions_pre
install -Dd -m 0750 %{buildroot}%{_sysconfdir}/salt/pki/master/minions_rejected
install -Dd -m 0750 %{buildroot}%{_sysconfdir}/salt/pki/minion
install -Dd -m 0750 %{buildroot}/srv/pillar
install -Dd -m 0750 %{buildroot}/srv/salt
install -Dd -m 0750 %{buildroot}/srv/spm
install -Dd -m 0750 %{buildroot}/var/lib/salt
install -Dd -m 0755 %{buildroot}%{_docdir}/salt
install -Dd -m 0755 %{buildroot}%{_sbindir}
%if 0%{?suse_version} > 1500
install -Dd -m 0755 %{buildroot}%{_distconfdir}/logrotate.d
%else
install -Dd -m 0755 %{buildroot}%{_sysconfdir}/logrotate.d
%endif

# Install salt-support profiles
%{python_expand #
install -Dpm 0644 salt/cli/support/profiles/* %{buildroot}%{$python_sitelib}/salt/cli/support/profiles
}

%endif

%if "%{flavor}" == "testsuite"
# Install Salt tests
%{python_expand #
install -Dd %{buildroot}%{$python_sitelib}/salt-testsuite
cp -a tests %{buildroot}%{$python_sitelib}/salt-testsuite/
# Remove runtests.py which is not used as deprecated method of running the tests
rm %{buildroot}%{$python_sitelib}/salt-testsuite/tests/runtests.py
# Copy conf files to the testsuite as they are used by the tests
cp -a conf %{buildroot}%{$python_sitelib}/salt-testsuite/
}
%endif

%if "%{flavor}" != "testsuite"

## Install Zypper plugins only on SUSE machines
%if 0%{?suse_version}
install -Dd -m 0750 %{buildroot}%{_prefix}/lib/zypp/plugins/commit
%{__install} scripts/suse/zypper/plugins/commit/zyppnotify %{buildroot}%{_prefix}/lib/zypp/plugins/commit/zyppnotify
%endif

# Install DNF plugin only on RH machines
%if 0%{?fedora} >= 22 || 0%{?rhel} >= 8
install -Dd %{buildroot}%{python3_sitelib}/dnf-plugins
install -Dd %{buildroot}%{python3_sitelib}/dnf-plugins/__pycache__
install -Dd %{buildroot}%{_sysconfdir}/dnf/plugins
%{__install} scripts/suse/dnf/plugins/dnfnotify.py %{buildroot}%{python3_sitelib}/dnf-plugins
%{__install} scripts/suse/dnf/plugins/dnfnotify.conf %{buildroot}%{_sysconfdir}/dnf/plugins
%{__python3} -m compileall -d %{python3_sitelib}/dnf-plugins %{buildroot}%{python3_sitelib}/dnf-plugins/dnfnotify.py
%{__python3} -O -m compileall -d %{python3_sitelib}/dnf-plugins %{buildroot}%{python3_sitelib}/dnf-plugins/dnfnotify.py
%endif

## install init and systemd scripts
%if %{with systemd}
install -Dpm 0644 pkg/old/suse/salt-master.service %{buildroot}%{_unitdir}/salt-master.service
%if 0%{?suse_version}
install -Dpm 0644 pkg/old/suse/salt-minion.service %{buildroot}%{_unitdir}/salt-minion.service
%else
install -Dpm 0644 pkg/old/suse/salt-minion.service.rhel7 %{buildroot}%{_unitdir}/salt-minion.service
%endif
install -Dpm 0644 pkg/common/salt-syndic.service %{buildroot}%{_unitdir}/salt-syndic.service
install -Dpm 0644 pkg/old/suse/salt-api.service    %{buildroot}%{_unitdir}/salt-api.service
install -Dpm 0644 pkg/common/salt-proxy@.service %{buildroot}%{_unitdir}/salt-proxy@.service
ln -s service %{buildroot}%{_sbindir}/rcsalt-master
ln -s service %{buildroot}%{_sbindir}/rcsalt-syndic
ln -s service %{buildroot}%{_sbindir}/rcsalt-minion
ln -s service %{buildroot}%{_sbindir}/rcsalt-api
install -Dpm 644 %{S:2}                   %{buildroot}/usr/lib/tmpfiles.d/salt.conf
%endif

#
## install config files
install -Dpm 0640 conf/minion %{buildroot}%{_sysconfdir}/salt/minion
touch  -m 0640 -r conf/minion %{buildroot}%{_sysconfdir}/salt/minion_id # ghost file
install -Dpm 0640 conf/master %{buildroot}%{_sysconfdir}/salt/master
install -Dpm 0640 conf/roster %{buildroot}%{_sysconfdir}/salt/roster
install -Dpm 0640 conf/cloud %{buildroot}%{_sysconfdir}/salt/cloud
install -Dpm 0640 conf/cloud.profiles %{buildroot}%{_sysconfdir}/salt/cloud.profiles
install -Dpm 0640 conf/cloud.providers %{buildroot}%{_sysconfdir}/salt/cloud.providers
install -Dpm 0640 transactional_update.conf %{buildroot}%{_sysconfdir}/salt/minion.d/transactional_update.conf
#
%if 0%{?suse_version} > 1500
install -Dpm 0644  pkg/old/suse/salt-common.logrotate %{buildroot}%{_distconfdir}/logrotate.d/salt
%else
install -Dpm 0644  pkg/old/suse/salt-common.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/salt
%endif
#
%if 0%{?suse_version} <= 1500
## install SuSEfirewall2 rules
install -Dpm 0644  pkg/old/suse/salt.SuSEfirewall2 %{buildroot}%{_sysconfdir}/sysconfig/SuSEfirewall2.d/services/salt
%endif
#
## install completion scripts
%if %{with bash_completion}
install -Dpm 0644 pkg/common/salt.bash %{buildroot}%{_sysconfdir}/bash_completion.d/salt
%endif
%if %{with zsh_completion}
install -Dpm 0644 pkg/common/salt.zsh %{buildroot}%{_sysconfdir}/zsh_completion.d/salt
%endif

%if %{with fish_completion}
mkdir -p %{buildroot}%{fish_completions_dir}
install -Dpm 0644 pkg/common/fish-completions/* %{buildroot}%{fish_completions_dir}
%endif

# Standalone Salt formulas configuration
install -Dd -m 0750 %{buildroot}%{_prefix}/share/salt-formulas
install -Dd -m 0750 %{buildroot}%{_prefix}/share/salt-formulas/states
install -Dd -m 0750 %{buildroot}%{_prefix}/share/salt-formulas/metadata
install -Dpm 0640 conf/suse/standalone-formulas-configuration.conf %{buildroot}%{_sysconfdir}/salt/master.d
install -Dpm 0640 conf/suse/standalone-formulas-configuration.conf %{buildroot}%{_sysconfdir}/salt/minion.d

%if 0%{?suse_version} > 1020
%fdupes %{buildroot}%{_docdir}
%python_expand %fdupes %{buildroot}%{$python_sitelib}
%endif

%if 0%{?_alternatives}
%python_clone -a %{buildroot}%{_bindir}/salt-call
%python_clone -a %{buildroot}%{_bindir}/salt-support
%python_clone -a %{buildroot}%{_bindir}/spm
install -Dd -m 0750 %{buildroot}%{_exec_prefix}/libexec/salt
for SALT_SCRIPT in salt salt-api salt-cloud salt-cp salt-key salt-master salt-minion salt-proxy salt-run salt-ssh salt-syndic; do
    mv "%{buildroot}%{_bindir}/${SALT_SCRIPT}" "%{buildroot}%{_exec_prefix}/libexec/salt/"
%python_clone -a %{buildroot}%{_exec_prefix}/libexec/salt/${SALT_SCRIPT}
    ln -s "%{_exec_prefix}/libexec/salt/${SALT_SCRIPT}" "%{buildroot}%{_bindir}/${SALT_SCRIPT}"
done
mv "%{buildroot}%{_prefix}/lib/zypp/plugins/commit/zyppnotify" "%{buildroot}%{_exec_prefix}/libexec/salt/"
%python_clone -a %{buildroot}%{_exec_prefix}/libexec/salt/zyppnotify
ln -s "%{_exec_prefix}/libexec/salt/zyppnotify" "%{buildroot}%{_prefix}/lib/zypp/plugins/commit/zyppnotify"
%endif

%endif

%check
%if %{with test}
%{python_expand #
$python setup.py test --runtests-opts=-u
}
%endif

%if "%{flavor}" != "testsuite"

%pre
S_HOME="/var/lib/salt"
S_PHOME="/srv/salt"
getent passwd salt | grep $S_PHOME >/dev/null && usermod -d $S_HOME salt
getent group salt >/dev/null || %{_sbindir}/groupadd -r salt
getent passwd salt >/dev/null || %{_sbindir}/useradd -r -g salt -d $S_HOME -s /bin/false -c "salt-master daemon" salt
if [[ -d "$S_PHOME/.ssh" ]]; then
    mv $S_PHOME/.ssh $S_HOME
fi
%if 0%{?suse_version} > 1500
# Prepare for migration to /usr/etc; save any old .rpmsave
test -f %{_sysconfdir}/logrotate.d/salt.rpmsave && mv -v %{_sysconfdir}/logrotate.d/salt.rpmsave %{_sysconfdir}/logrotate.d/salt.rpmsave.old ||:
%endif

%post
%if %{with systemd}
systemd-tmpfiles --create /usr/lib/tmpfiles.d/salt.conf || true
%else
dbus-uuidgen --ensure
%endif

%if 0%{?suse_version} > 1500
%posttrans
# Migration to /usr/etc, restore just created .rpmsave
test -f %{_sysconfdir}/logrotate.d/salt.rpmsave && mv -v %{_sysconfdir}/logrotate.d/salt.rpmsave %{_sysconfdir}/logrotate.d/salt ||:
test -f %{_sysconfdir}/logrotate.d/salt.rpmsave.old && mv -v %{_sysconfdir}/logrotate.d/salt.rpmsave.old %{_sysconfdir}/logrotate.d/salt.rpmsave ||:
%endif

%preun proxy
%if %{with systemd}
%if 0%{?suse_version}
%service_del_preun salt-proxy@.service
%else
%systemd_preun salt-proxy@.service
%endif
%else
%if 0%{?suse_version}
%stop_on_removal salt-proxy
%endif
%endif

%pre proxy
%if %{with systemd}
%if 0%{?suse_version}
%service_add_pre salt-proxy@.service
%endif
%endif

%post proxy
%if %{with systemd}
%if 0%{?suse_version}
%service_add_post salt-proxy@.service
%else
%systemd_post salt-proxy@.service
%endif
%endif

%postun proxy
%if %{with systemd}
%if 0%{?suse_version}
%service_del_postun salt-proxy@.service
%else
%systemd_postun_with_restart salt-proxy@.service
%endif
%endif

%preun syndic
%if %{with systemd}
%if 0%{?suse_version}
%service_del_preun salt-syndic.service
%else
%systemd_preun salt-syndic.service
%endif
%endif

%pre syndic
%if %{with systemd}
%if 0%{?suse_version}
%service_add_pre salt-syndic.service
%endif
%endif

%post syndic
%if %{with systemd}
%if 0%{?suse_version}
%service_add_post salt-syndic.service
%else
%systemd_post salt-syndic.service
%endif
%endif

%postun syndic
%if %{with systemd}
%if 0%{?suse_version}
%service_del_postun salt-syndic.service
%else
%systemd_postun_with_restart salt-syndic.service
%endif
%endif

%preun master
%if %{with systemd}
%if 0%{?suse_version}
%service_del_preun salt-master.service
%else
%systemd_preun salt-master.service
%endif
%endif

%pre master
%if %{with systemd}
%if 0%{?suse_version}
%service_add_pre salt-master.service
%endif
%endif

%post master
if [ $1 -eq 2 ] ; then
  # Upgrading from an earlier version.  If this is from 2014, where daemons
  # ran as root, we need to chown some stuff to salt in order for the new
  # version to actually work.  It seems a manual restart of salt-master may
  # still be required, but at least this will actually work given the file
  # ownership is correct.
  # Symlinks are excluded to avoid possible user escalation (bsc#1157465) (CVE-2019-18897).
  for file in master.{pem,pub} ; do
    [ -f /etc/salt/pki/master/$file ] && [ ! -L /etc/salt/pki/master/$file ] && chown --no-dereference salt /etc/salt/pki/master/$file
  done
  MASTER_CACHE_DIR="/var/cache/salt/master"
  [ -d $MASTER_CACHE_DIR ] && find $MASTER_CACHE_DIR -type d | xargs -r chown --no-dereference salt:salt
  [ -d $MASTER_CACHE_DIR ] && find $MASTER_CACHE_DIR -type f | xargs -r chown --no-dereference salt:salt
  [ -f $MASTER_CACHE_DIR/.root_key ] && chown --no-dereference root:root $MASTER_CACHE_DIR/.root_key
  true
fi
%if %{with systemd}
systemd_ver=$(rpm -q systemd --queryformat="%%{VERSION}")
if [ "${systemd_ver%%.*}" -lt 228 ]; then
  # On systemd < 228 the 'TasksTask' attribute is not available.
  # Removing TasksMax from salt-master.service on SLE12SP1 LTSS (bsc#985112)
  sed -i '/TasksMax=infinity/d' %{_unitdir}/salt-master.service
fi
%if 0%{?suse_version}
%service_add_post salt-master.service
%else
%systemd_post salt-master.service
%endif
%endif

%postun master
%if %{with systemd}
%if 0%{?suse_version}
%service_del_postun salt-master.service
%else
%systemd_postun_with_restart salt-master.service
%endif
%endif

%preun minion
%if %{with systemd}
%if 0%{?suse_version}
%service_del_preun salt-minion.service
%else
%systemd_preun salt-minion.service
%endif
%endif

%pre minion
%if %{with systemd}
%if 0%{?suse_version}
%service_add_pre salt-minion.service
%endif
%endif

%post minion
%if %{with systemd}
%if 0%{?suse_version}
%service_add_post salt-minion.service
%else
%systemd_post salt-minion.service
%endif
%endif

%postun minion
%if %{with systemd}
%if 0%{?suse_version}
%service_del_postun salt-minion.service
%else
%systemd_postun_with_restart salt-minion.service
%endif
%endif

%preun api
%if %{with systemd}
%if 0%{?suse_version}
%service_del_preun salt-api.service
%else
%systemd_preun salt-api.service
%endif
%else
%stop_on_removal
%endif

%pre api
%if %{with systemd}
%if 0%{?suse_version}
%service_add_pre salt-api.service
%endif
%endif

%post api
%if %{with systemd}
%if 0%{?suse_version}
%service_add_post salt-api.service
%else
%systemd_post salt-api.service
%endif
%endif

%postun api
%if %{with systemd}
%if 0%{?suse_version}
%service_del_postun salt-api.service
%else
%systemd_postun_with_restart salt-api.service
%endif
%endif

%if 0%{?_alternatives}
%pre -n python-salt
for SALT_SCRIPT in salt-call salt-support spm; do
    [ -h "%{_bindir}/${SALT_SCRIPT}" ] || rm -f "%{_bindir}/${SALT_SCRIPT}"
    if [ "$1" -gt 0 ] && [ -f /usr/sbin/update-alternatives ]; then
        update-alternatives --quiet --remove "${SALT_SCRIPT}" "%{_bindir}/${SALT_SCRIPT}-%{python_bin_suffix}"
    fi
done
for SALT_SCRIPT in salt salt-api salt-cloud salt-cp salt-key salt-master salt-minion salt-proxy salt-run salt-ssh salt-syndic zyppnotify; do
    [ -h "%{_exec_prefix}/libexec/salt/${SALT_SCRIPT}" ] || rm -f "%{_exec_prefix}/libexec/salt/${SALT_SCRIPT}"
    if [ "$1" -gt 0 ] && [ -f /usr/sbin/update-alternatives ]; then
        update-alternatives --quiet --remove "${SALT_SCRIPT}" "%{_exec_prefix}/libexec/salt/${SALT_SCRIPT}-%{python_bin_suffix}"
    fi
done

%if ! %{with libalternatives}
%post -n python-salt
if [ -f /usr/sbin/update-alternatives ]; then
    for SALT_SCRIPT in salt-call salt-support spm; do
        update-alternatives --quiet --install "%{_bindir}/${SALT_SCRIPT}" "${SALT_SCRIPT}" \
            "%{_bindir}/${SALT_SCRIPT}-%{python_bin_suffix}" %{python_version_nodots}
    done
    for SALT_SCRIPT in salt salt-api salt-cloud salt-cp salt-key salt-master salt-minion salt-proxy salt-run salt-ssh salt-syndic zyppnotify; do
        update-alternatives --quiet --install "%{_exec_prefix}/libexec/salt/${SALT_SCRIPT}" "${SALT_SCRIPT}" \
            "%{_exec_prefix}/libexec/salt/${SALT_SCRIPT}-%{python_bin_suffix}" %{python_version_nodots}
    done
fi

%postun -n python-salt
if [ -f /usr/sbin/update-alternatives ]; then
    for SALT_SCRIPT in salt-call salt-support spm; do
        if [ ! -e "%{_bindir}/${SALT_SCRIPT}-%{python_bin_suffix}" ]; then
            update-alternatives --quiet --remove "${SALT_SCRIPT}" "%{_bindir}/${SALT_SCRIPT}-%{python_bin_suffix}"
        fi
    done
    for SALT_SCRIPT in salt salt-api salt-cloud salt-cp salt-key salt-master salt-minion salt-proxy salt-run salt-ssh salt-syndic zyppnotify; do
        if [ ! -e "%{_exec_prefix}/libexec/salt/${SALT_SCRIPT}-%{python_bin_suffix}" ]; then
            update-alternatives --quiet --remove "${SALT_SCRIPT}" "%{_exec_prefix}/libexec/salt/${SALT_SCRIPT}-%{python_bin_suffix}"
        fi
    done
fi
%endif
%endif

%if 0%{?singlespec_compat}
%posttrans -n %{python_module salt}
%else
%posttrans -n python-salt
%endif

%if %{with libalternatives}
# restore symlinks to alts after migration from update-alternatives to alts
# in cases where the old package flavor (based u-a) is removed in favor of
# new python flavor (bsc#1250755).
# i.a. python3-salt (3.6 using u-a) -> python313-salt (3.13 using alts)
if [ -f /usr/bin/alts ]; then
    for SALT_SCRIPT in salt-call salt-support spm; do
        if [ ! -e "%{_bindir}/${SALT_SCRIPT}" ]; then
            ln -sf alts "%{_bindir}/${SALT_SCRIPT}"
        fi
    done
    for SALT_SCRIPT in salt salt-api salt-cloud salt-cp salt-key salt-master salt-minion salt-proxy salt-run salt-ssh salt-syndic zyppnotify; do
        if [ ! -e "%{_exec_prefix}/libexec/salt/${SALT_SCRIPT}" ]; then
            ln -sf ../../bin/alts "%{_exec_prefix}/libexec/salt/${SALT_SCRIPT}"
        fi
    done
fi
%endif

# force re-generate a new thin.tgz
rm -f %{_localstatedir}/cache/salt/master/thin/version
rm -f %{_localstatedir}/cache/salt/minion/thin/version

%files api
%defattr(-,root,root)
%{_bindir}/salt-api
%if %{with systemd}
%{_sbindir}/rcsalt-api
%{_unitdir}/salt-api.service
%endif
%{_mandir}/man1/salt-api.1.*

%files cloud
%defattr(-,root,root)
%{_bindir}/salt-cloud
%dir               %attr(0750, root, salt) %{_sysconfdir}/salt/cloud.maps.d
%dir               %attr(0750, root, salt) %{_sysconfdir}/salt/cloud.profiles.d
%dir               %attr(0750, root, salt) %{_sysconfdir}/salt/cloud.providers.d
%config(noreplace) %attr(0640, root, salt) %{_sysconfdir}/salt/cloud
%config(noreplace) %attr(0640, root, salt) %{_sysconfdir}/salt/cloud.profiles
%config(noreplace) %attr(0640, root, salt) %{_sysconfdir}/salt/cloud.providers
%dir               %attr(0750, root, salt) %{_localstatedir}/cache/salt/cloud
%{_mandir}/man1/salt-cloud.1.*

%files ssh
%defattr(-,root,root)
%{_bindir}/salt-ssh
%{_mandir}/man1/salt-ssh.1.gz

%files syndic
%defattr(-,root,root)
%{_bindir}/salt-syndic
%{_mandir}/man1/salt-syndic.1.gz
%if %{with systemd}
%{_sbindir}/rcsalt-syndic
%{_unitdir}/salt-syndic.service
%endif

%files minion
%defattr(-,root,root)
%{_bindir}/salt-minion
%{_mandir}/man1/salt-minion.1.gz
%config(noreplace) %attr(0640, root, root) %{_sysconfdir}/salt/minion
%config(noreplace) %attr(0640, root, root) %ghost %{_sysconfdir}/salt/minion_id
%dir               %attr(0750, root, root) %{_sysconfdir}/salt/minion.d/
%dir               %attr(0750, root, root) %{_sysconfdir}/salt/pki/minion/
%dir               %attr(0750, root, root) %{_localstatedir}/cache/salt/minion/
%if %{with systemd}
%{_sbindir}/rcsalt-minion
%endif

# Install plugin only on SUSE machines
%if 0%{?suse_version}
%{_prefix}/lib/zypp/plugins/commit/zyppnotify
%endif

# Install DNF plugin only on RH machines
%if 0%{?fedora} >= 22 || 0%{?rhel} >= 8
%{python3_sitelib}/dnf-plugins/dnfnotify.py
%{python3_sitelib}/dnf-plugins/__pycache__/dnfnotify.*
%{_sysconfdir}/dnf/plugins/dnfnotify.conf
%endif

%if %{with systemd}
%{_unitdir}/salt-minion.service
%endif

%files proxy
%defattr(-,root,root)
%{_bindir}/salt-proxy
%{_mandir}/man1/salt-proxy.1.gz
%if %{with systemd}
%{_unitdir}/salt-proxy@.service
%endif

%files master
%defattr(-,root,root)
%{_bindir}/salt
%{_bindir}/salt-master
%{_bindir}/salt-cp
%{_bindir}/salt-key
%{_bindir}/salt-run
%{_mandir}/man1/salt-master.1.gz
%{_mandir}/man1/salt-cp.1.gz
%{_mandir}/man1/salt-key.1.gz
%{_mandir}/man1/salt-run.1.gz
%{_mandir}/man7/salt.7.gz
%if 0%{?suse_version} <= 1500
%config(noreplace) %{_sysconfdir}/sysconfig/SuSEfirewall2.d/services/salt
%endif
%if %{with systemd}
%{_sbindir}/rcsalt-master
%{_unitdir}/salt-master.service
%endif
#
%config(noreplace) %attr(0640, root, salt) %{_sysconfdir}/salt/master
%config(noreplace) %attr(0640, root, salt) %{_sysconfdir}/salt/roster
%dir               %attr(0755, root, salt) %{_sysconfdir}/salt/master.d/
%dir               %attr(0750, salt, salt) %{_sysconfdir}/salt/pki/master/
%dir               %attr(0750, salt, salt) %{_sysconfdir}/salt/pki/master/minions/
%dir               %attr(0750, salt, salt) %{_sysconfdir}/salt/pki/master/minions_autosign/
%dir               %attr(0750, salt, salt) %{_sysconfdir}/salt/pki/master/minions_denied/
%dir               %attr(0750, salt, salt) %{_sysconfdir}/salt/pki/master/minions_pre/
%dir               %attr(0750, salt, salt) %{_sysconfdir}/salt/pki/master/minions_rejected/
%dir               %attr(0755, salt, salt) /var/lib/salt
%dir               %attr(0755, root, salt) /srv/salt
%dir               %attr(0755, root, salt) /srv/pillar
%dir               %attr(0750, salt, salt) %{_localstatedir}/cache/salt/master/
%dir               %attr(0750, salt, salt) %{_localstatedir}/cache/salt/master/jobs/
%dir               %attr(0750, salt, salt) %{_localstatedir}/cache/salt/master/proc/
%dir               %attr(0750, salt, salt) %{_localstatedir}/cache/salt/master/queues/
%dir               %attr(0750, salt, salt) %{_localstatedir}/cache/salt/master/roots/
%dir               %attr(0750, salt, salt) %{_localstatedir}/cache/salt/master/syndics/
%dir               %attr(0750, salt, salt) %{_localstatedir}/cache/salt/master/tokens/

%files
%defattr(-,root,root,-)
%{_bindir}/spm
%if ! 0%{?_alternatives}
%{_bindir}/salt-call
%endif
%{_bindir}/salt-support
%{_mandir}/man1/salt-call.1.gz
%{_mandir}/man1/spm.1.gz
%if 0%{?suse_version} > 1500
%{_distconfdir}/logrotate.d/salt
%else
%config(noreplace) %{_sysconfdir}/logrotate.d/salt
%endif
%{!?_licensedir:%global license %doc}
%license LICENSE
%doc AUTHORS README.rst README.SUSE
#
%dir        %attr(0750, root, salt) %{_sysconfdir}/salt
%dir        %attr(0750, root, salt) %{_sysconfdir}/salt/pki
%dir        %attr(0750, salt, salt) %{_localstatedir}/log/salt
%dir        %attr(0750, root, salt) %{_localstatedir}/cache/salt
%dir        %attr(0750, root, salt) /srv/spm
%if %{with systemd}
/usr/lib/tmpfiles.d/salt.conf
%endif
%{_mandir}/man1/salt.1.*

%files %{python_files salt}
%defattr(-,root,root,-)
%if 0%{?_alternatives}
%python_alternative %{_bindir}/salt-call
%python_alternative %{_bindir}/salt-support
%python_alternative %{_bindir}/spm
%dir %{_exec_prefix}/libexec
%dir %attr(0755, root, root) %{_exec_prefix}/libexec/salt
%python_alternative %{_exec_prefix}/libexec/salt/salt
%python_alternative %{_exec_prefix}/libexec/salt/salt-api
%python_alternative %{_exec_prefix}/libexec/salt/salt-cloud
%python_alternative %{_exec_prefix}/libexec/salt/salt-cp
%python_alternative %{_exec_prefix}/libexec/salt/salt-key
%python_alternative %{_exec_prefix}/libexec/salt/salt-master
%python_alternative %{_exec_prefix}/libexec/salt/salt-minion
%python_alternative %{_exec_prefix}/libexec/salt/salt-proxy
%python_alternative %{_exec_prefix}/libexec/salt/salt-run
%python_alternative %{_exec_prefix}/libexec/salt/salt-ssh
%python_alternative %{_exec_prefix}/libexec/salt/salt-syndic
%python_alternative %{_exec_prefix}/libexec/salt/zyppnotify
%endif

%dir %{python_sitelib}/salt
%dir %{python_sitelib}/salt-*.egg-info
%{python_sitelib}/salt/*
%{python_sitelib}/salt-*.egg-info/*

%if %{with docs}
%files doc
%defattr(-,root,root)
%doc doc/_build/html
%endif

%if %{with bash_completion}
%files bash-completion
%defattr(-,root,root)
%dir %{_sysconfdir}/bash_completion.d/
%config %{_sysconfdir}/bash_completion.d/%{name}
%endif

%if %{with zsh_completion}
%files zsh-completion
%defattr(-,root,root)
%dir %{_sysconfdir}/zsh_completion.d/
%config %{_sysconfdir}/zsh_completion.d/%{name}
%endif

%if %{with fish_completion}
%files fish-completion
%defattr(-,root,root)
%{fish_completions_dir}/salt*
%dir %{fish_completions_dir}
%dir %{fish_dir}
%endif

%files standalone-formulas-configuration
%defattr(-,root,root)
%dir               %attr(0755, root, salt) %{_sysconfdir}/salt/master.d/
%config(noreplace) %attr(0640, root, salt) %{_sysconfdir}/salt/master.d/standalone-formulas-configuration.conf
%dir               %attr(0750, root, root) %{_sysconfdir}/salt/minion.d/
%config(noreplace) %attr(0640, root, root) %{_sysconfdir}/salt/minion.d/standalone-formulas-configuration.conf
%dir               %attr(0755, root, salt) %{_prefix}/share/salt-formulas/
%dir               %attr(0755, root, salt) %{_prefix}/share/salt-formulas/states/
%dir               %attr(0755, root, salt) %{_prefix}/share/salt-formulas/metadata/

%files transactional-update
%defattr(-,root,root)
%config(noreplace) %attr(0640, root, root) %{_sysconfdir}/salt/minion.d/transactional_update.conf

%endif

%if "%{flavor}" == "testsuite"
%files %{python_files salt-testsuite}
%{python_sitelib}/salt-testsuite
%endif

%changelog
