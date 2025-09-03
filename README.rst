.. image:: https://img.shields.io/github/license/saltstack/salt
   :alt: Salt Project License: Apache v2.0
   :target: https://github.com/openSUSE/salt/blob/master/LICENSE

.. image:: https://img.shields.io/twitch/status/saltprojectoss
   :alt: Salt Project Twitch Channel
   :target: https://www.twitch.tv/saltprojectoss

.. image:: https://img.shields.io/reddit/subreddit-subscribers/saltstack?style=social
   :alt: Salt Project subreddit
   :target: https://www.reddit.com/r/saltstack/

.. image:: https://img.shields.io/twitter/follow/Salt_Project_OS?style=social&logo=twitter
   :alt: Follow SaltStack on Twitter
   :target: https://twitter.com/intent/follow?screen_name=Salt_Project_OS

.. figure:: https://gitlab.com/saltstack/open/salt-branding-guide/-/raw/master/logos/SaltProject_altlogo_teal.png?inline=true
   :scale: 80 %
   :width: 1000px
   :height: 356px
   :align: center
   :alt: Salt Project Logo

* `Latest Salt Documentation`_
* `Open an issue <https://github.com/openSUSE/salt/issues/new/choose>`_ (bug report, feature request, etc.)

*Salt is the world's fastest, most intelligent and scalable automation*
*engine.*

About Salt
==========
Built on Python, Salt is an event-driven automation tool and framework to
deploy, configure, and manage complex IT systems. Use Salt to automate common
infrastructure administration tasks and ensure that all the components of your
infrastructure are operating in a consistent desired state.

Salt has many possible uses, including configuration management, which involves:

* Managing operating system deployment and configuration.
* Installing and configuring software applications and services.
* Managing servers, virtual machines, containers, databases, web servers,
  network devices, and more.
* Ensuring consistent configuration and preventing configuration drift.

Salt is ideal for configuration management because it is pluggable,
customizable, and plays well with many existing technologies. Salt enables you
to deploy and manage applications that use any tech stack running on nearly any
`operating system <https://docs.saltproject.io/salt/install-guide/en/latest/topics/salt-supported-operating-systems.html>`_,
including different types of network devices such as switches and routers from a
variety of vendors.

In addition to configuration management Salt can also:

* Automate and orchestrate routine IT processes, such as common required tasks
  for scheduled server downtimes or upgrading operating systems or applications.
* Create self-aware, self-healing systems that can automatically respond to
  outages, common administration problems, or other important events.


Download and install Salt
=========================
Salt is distributed for most currently supported SUSE and openSUSE operating systems.

Execute the following commands to install Salt:

.. code-block:: shell

   zypper ref
   zypper install salt salt-master salt-minion


Technical support
=================
Report bugs or problems using Salt by opening an issue: `<https://github.com/openSUSE/salt/issues>`_


Salt Project documentation
==========================
Installation instructions, tutorials, in-depth API and module documentation:

* `The Salt user guide <https://docs.saltproject.io/salt/user-guide/en/latest/>`_
* `Latest Salt documentation <https://docs.saltproject.io/en/latest/contents.html>`_
* `Salt's contributing guide <https://docs.saltproject.io/en/master/topics/development/contributing.html>`_


Security advisories
===================
For reporting security issues, see
`SUSE Security Contacts <https://www.suse.com/support/security/contact/>`_.

For receiving security reports, see the
`openSUSE/SUSE Security Announce mailing list <https://lists.opensuse.org/archives/list/security-announce@lists.opensuse.org/>`_.

Keep an eye on the Salt Project
`Security Announcements <https://saltproject.io/security-announcements/>`_
landing page. Salt Project recommends subscribing to the
`Salt Project Security RSS feed <https://saltproject.io/feed/?post_type=security>`_
to receive notification when new information is available regarding security
announcements.


License
=======
Salt is licensed under the Apache 2.0 license. Please
see the
`LICENSE file <https://github.com/openSUSE/salt/blob/master/LICENSE>`_ for the
full text of the Apache license, followed by a full summary of the licensing
used by external modules.

A complete list of attributions and dependencies can be found here:
`salt/DEPENDENCIES.md <https://github.com/openSUSE/salt/blob/master/DEPENDENCIES.md>`_
