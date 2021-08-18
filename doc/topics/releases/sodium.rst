:orphan:

====================================
Salt Release Notes - Codename Sodium
====================================


Salt mine updates
=================

Syntax update
-------------

The syntax for defining salt functions in config or pillar files has changed to
also support the syntax used in :py:mod:`module.run <salt.states.module.run>`.
The old syntax for the mine_function - as a dict, or as a list with dicts that
contain more than exactly one key - is still supported but discouraged in favor
of the more uniform syntax of module.run.


State updates
=============

The ``creates`` state requisite has been migrated from the
:mod:`docker_container <salt.states.docker_container>` and :mod:`cmd <salt.states.cmd>`
states to become a global option. This acts similar to an equivalent
``unless: test -f filename`` but can also accept a list of filenames. This allows
all states to take advantage of the enhanced functionality released in Neon, of allowing
salt execution modules for requisite checks.
