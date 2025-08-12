==========================================
Community Proxmox Collection Release Notes
==========================================

.. contents:: Topics

v1.3.0
======

Release Summary
---------------

This is the minor release of the ``community.proxmox`` collection.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release.

Minor Changes
-------------

- proxmox* modules - added fallback environment variables for ``api_token``, ``api_secret``, and ``validate_certs`` (https://github.com/ansible-collections/community.proxmox/issues/63, https://github.com/ansible-collections/community.proxmox/pull/136).
- proxmox_cluster_ha_groups - fix idempotency in proxmox_cluster_ha_groups module (https://github.com/ansible-collections/community.proxmox/issues/138, https://github.com/ansible-collections/community.proxmox/pull/139).
- proxmox_cluster_ha_resources -  Fix idempotency proxmox_cluster_ha_resources (https://github.com/ansible-collections/community.proxmox/pull/135).
- proxmox_kvm - Add missing 'storage' parameter to create_vm()-call.
- proxmox_kvm - add new purge parameter to proxmox_kvm module (https://github.com/ansible-collections/community.proxmox/issues/60, https://github.com/ansible-collections/community.proxmox/pull/148).

Bugfixes
--------

- proxmox_pct_remote connection plugin - avoid deprecated ansible-core paramiko import helper, import paramiko directly instead (https://github.com/ansible-collections/community.proxmox/issues/146, https://github.com/ansible-collections/community.proxmox/pull/151).

New Modules
-----------

- community.proxmox.proxmox_storage - Manage storage in PVE clusters and nodes.

v1.2.0
======

Release Summary
---------------

This is the minor release of the ``community.proxmox`` collection.
This changelog contains all changes to the modules and plugins in this collection that have been made after the previous release.

Minor Changes
-------------

- proxmox inventory plugin - always provide basic information regardless of want_facts (https://github.com/ansible-collections/community.proxmox/pull/124).
- proxmox_cluster - cluster creation has been made idempotent (https://github.com/ansible-collections/community.proxmox/pull/125).
- proxmox_pct_remote - allow forward agent with paramiko (https://github.com/ansible-collections/community.proxmox/pull/130).

New Modules
-----------

- community.proxmox.proxmox_group - Group management for Proxmox VE cluster.
- community.proxmox.proxmox_node - Manage Proxmox VE nodes.
- community.proxmox.proxmox_user - User management for Proxmox VE cluster.

v1.1.0
======

Release Summary
---------------

This is the minor release of the ``community.proxmox`` collection.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release.

Minor Changes
-------------

- proxmox - allow force deletion of LXC containers (https://github.com/ansible-collections/community.proxmox/pull/105).
- proxmox - validate the cluster name length (https://github.com/ansible-collections/community.proxmox/pull/119).

Bugfixes
--------

- proxmox inventory plugin - avoid using deprecated option when templating options (https://github.com/ansible-collections/community.proxmox/pull/108).

New Modules
-----------

- community.proxmox.proxmox_access_acl - Management of ACLs for objects in Proxmox VE Cluster.
- community.proxmox.proxmox_cluster_ha_groups - Management of HA groups in Proxmox VE Cluster.
- community.proxmox.proxmox_cluster_ha_resources - Management of HA groups in Proxmox VE Cluster.

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
