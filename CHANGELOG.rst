==========================================
Community Proxmox Collection Release Notes
==========================================

.. contents:: Topics

v1.0.1
======

Release Summary
---------------

This is a minor bugfix release for the ``community.proxmox`` collections.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release.

Minor Changes
-------------

- proxmox module utils - fix handling warnings in LXC tasks (https://github.com/ansible-collections/community.proxmox/pull/104).

v1.0.0
======

Release Summary
---------------

This is the first stable release of the ``community.proxmox`` collection since moving from ``community.general``, released on 2025-06-08.

Minor Changes
-------------

- proxmox - add support for creating and updating containers in the same task (https://github.com/ansible-collections/community.proxmox/pull/92).
- proxmox module util - do not hang on tasks that throw warnings (https://github.com/ansible-collections/community.proxmox/issues/96, https://github.com/ansible-collections/community.proxmox/pull/100).
- proxmox_kvm - add ``rng0`` option to specify an RNG device (https://github.com/ansible-collections/community.proxmox/pull/18).
- proxmox_kvm - remove redundant check for duplicate names as this is allowed by PVE API (https://github.com/ansible-collections/community.proxmox/issues/97, https://github.com/ansible-collections/community.proxmox/pull/99).
- proxmox_snap - correctly handle proxmox_snap timeout parameter (https://github.com/ansible-collections/community.proxmox/issues/73, https://github.com/ansible-collections/community.proxmox/issues/95, https://github.com/ansible-collections/community.proxmox/pull/101).

Breaking Changes / Porting Guide
--------------------------------

- proxmox - ``update`` and ``force`` are now mutually exclusive (https://github.com/ansible-collections/community.proxmox/pull/92).
- proxmox - the default of ``update`` changed from ``false`` to ``true`` (https://github.com/ansible-collections/community.proxmox/pull/92).

Bugfixes
--------

- proxmox - fix crash in module when the used on an existing LXC container with ``state=present`` and ``force=true`` (https://github.com/ansible-collections/community.proxmox/pull/91).

New Modules
-----------

- community.proxmox.proxmox_backup_schedule - Schedule VM backups and removing them.
- community.proxmox.proxmox_cluster - Create and join Proxmox VE clusters.
- community.proxmox.proxmox_cluster_join_info - Retrieve the join information of the Proxmox VE cluster.

v0.1.0
======

Release Summary
---------------

This is the first community.proxmox release. It contains mainly the state of the Proxmox content in community.general 10.6.0.
The minimum required ansible-core version for community.proxmox is ansible-core 2.17, which implies Python 3.7+.
The minimum required proxmoxer version is 2.0.0.
