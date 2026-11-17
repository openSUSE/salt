.. _blackout:

=============================
Minion Blackout Configuration
=============================

.. versionadded:: 2016.3.0

Salt supports minion blackouts. When a minion is in blackout mode, all remote
execution commands are disabled. This allows production minions to be put
"on hold", eliminating the risk of an untimely configuration change.

Minion blackouts are configured via a special pillar key, ``minion_blackout``.
If this key is set to ``True``, then the minion will reject all incoming
commands, except for ``saltutil.refresh_pillar``. (The exception is important,
so minions can be brought out of blackout mode)

Salt also supports an explicit whitelist of additional functions that will be
allowed during blackout. This is configured with the special pillar key
``minion_blackout_whitelist``, which is formed as a list:

.. code-block:: yaml

    minion_blackout_whitelist:
     - test.version
     - pillar.get

The whitelist only matches function names, so whitelisting ``state.apply`` would
allow any state to run. To restrict ``state.apply`` and ``state.sls`` to specific
SLS files, use ``minion_blackout_state_whitelist`` (pillar or grains) together
with ``minion_blackout_whitelist``:

.. code-block:: yaml

    minion_blackout: True
    minion_blackout_whitelist:
     - state.apply
    minion_blackout_state_whitelist:
     - packages.profileupdate

With this configuration ``state.apply packages.profileupdate`` runs, while a
bare ``state.apply`` (highstate) or any other SLS is rejected. If
``minion_blackout_state_whitelist`` is not set, the behavior is unchanged.
