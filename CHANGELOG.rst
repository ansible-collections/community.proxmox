==========================================
Community Proxmox Collection Release Notes
==========================================

.. contents:: Topics

v2.1.0
======

Release Summary
---------------

See https://github.com/ansible-collections/community.proxmox/blob/main/CHANGELOG.rst for all changes.

Minor Changes
-------------

- inventory - allow to customize generated ansible_hostname (https://github.com/ansible-collections/community.proxmox/pull/471).
- inventory plugin - add api_timeout option for Proxmox API requests and keep hosts in inventory when optional LXC/QEMU fact gathering fails (https://github.com/ansible-collections/community.proxmox/pull/257).
- inventory plugin - add exclude_vms option (https://github.com/ansible-collections/community.proxmox/pull/257).
- inventory plugin - add facts_concurrency option for concurrent LXC/QEMU fact gathering (https://github.com/ansible-collections/community.proxmox/pull/257).
- inventory plugin - fetch QEMU and LXC inventory records from /api2/json/cluster/resources?type=vm instead of querying every online node (https://github.com/ansible-collections/community.proxmox/pull/257).
- inventory plugin - fetch nodes from /api2/json/cluster/status instead of /api2/json/nodes (https://github.com/ansible-collections/community.proxmox/pull/257).
- proxmox - add ``mount_devices`` option to allow mounting passthrough devices for LXC containers. Note that Proxmox currently requires root@pam password login to manage passthrough devices (https://github.com/ansible-collections/community.proxmox/pull/506).
- proxmox - make ``api_host`` optional to support ``local`` backend (https://github.com/ansible-collections/community.proxmox/pull/349).
- proxmox - make ``api_user`` optional and default to ``root@pam`` (https://github.com/ansible-collections/community.proxmox/pull/349).
- proxmox - use ``local`` backend if no ``api_host`` is specified (https://github.com/ansible-collections/community.proxmox/pull/349).
- proxmox_ceph_pool - add ``application`` parameter to configure Ceph pool profile (``rbd``, ``cephfs``, ``rgw``), defaulting to ``rbd`` (https://github.com/ansible-collections/community.proxmox/issues/523).
- proxmox_cluster - add support for optional ``nodeid`` parameter during cluster creation and join operations.
- proxmox_cluster_firewall - rename to proxmox_cluster_firewall_options (https://github.com/ansible-collections/community.proxmox/issues/450).
- proxmox_domain - add ``openid_audiences`` parameter introduced in Proxmox VE 9.2 (https://github.com/ansible-collections/community.proxmox/pull/437).
- proxmox_kvm - add ``allow_ksm`` parameter to control the Proxmox VE ``allow-ksm`` QEMU option.
- proxmox_nic - increase max queues to 64 (https://github.com/ansible-collections/community.proxmox/pull/468).
- proxmox_node_firewall - rename to proxmox_node_firewall_options (https://github.com/ansible-collections/community.proxmox/issues/450).
- proxmox_node_firewall_info - rename to proxmox_node_firewall_options_info (https://github.com/ansible-collections/community.proxmox/issues/450).
- proxmox_pct_remote connection plugin - the ``password`` and ``token_secret`` options are now marked as ``secret=true`` for ansible-core 2.22+'s secret masking (https://github.com/ansible-collections/community.proxmox/pull/535).
- proxmox_pct_remote connection plugin - the ``password`` option is now marked as ``secret=true`` for ansible-core 2.22+'s secret masking (https://github.com/ansible-collections/community.proxmox/pull/535).
- proxmox_pool_member - add ``allow_move`` parameter to allow adding a guest even if already in another pool (https://github.com/ansible-collections/community.proxmox/pull/467).
- proxmox_qemu_api - adds extra debug logging (exceptions) when trying to connect to guest agent (https://github.com/ansible-collections/community.proxmox/pull/460).
- proxmox_qemu_api connection plugin - the ``api_password`` and ``api_token_secret`` options are now marked as ``secret=true`` for ansible-core 2.22+'s secret masking (https://github.com/ansible-collections/community.proxmox/pull/535).
- proxmox_storage - add  common storage properties ``shared``, ``prune_backups``, ``format`` and ``preallocation`` (https://github.com/ansible-collections/community.proxmox/pull/476).
- proxmox_storage - add diff mode functionality (https://github.com/ansible-collections/community.proxmox/pull/476).
- proxmox_storage - add support for ``btrfs``, ``esxi``, ``iscsidirect`` and ``zfs`` storage types (https://github.com/ansible-collections/community.proxmox/pull/476).
- proxmox_storage - add support for ``lvm`` and  ``lvm-thin`` storage types (https://github.com/ansible-collections/community.proxmox/issues/158).
- proxmox_storage - add update functionality (https://github.com/ansible-collections/community.proxmox/pull/476).

Deprecated Features
-------------------

- proxmox_cluster_firewall - add deprecation notice for ``proxmox_cluster_firewall`` module. This module will be renamed to ``proxmox_cluster_firewall_options`` in 3.0.0.
- proxmox_cluster_firewall_security_group - the default of ``purge_omitted_rule_fields`` will change from ``false`` to ``true`` in community.proxmox 3.0.0. With ``true``, optional rule fields that are omitted from a ``rules`` entry are removed from the existing rule. Set ``purge_omitted_rule_fields=false`` to keep preserving omitted rule fields in 3.0.0 (https://github.com/ansible-collections/community.proxmox/issues/278, https://github.com/ansible-collections/community.proxmox/pull/527).
- proxmox_node_firewall - add deprecation notice for ``proxmox_node_firewall`` module. This module will be renamed to ``proxmox_node_firewall_options`` in 3.0.0.
- proxmox_node_firewall_info - add deprecation notice for ``proxmox_node_firewall_info`` module. This module will be renamed to ``proxmox_node_firewall_options_info`` in 3.0.0.

Bugfixes
--------

- All modules - support both API token authentication formats: ``api_token_id: username@realm!tokenid`` (recommended) and ``api_user: username@realm`` with ``api_token_id: tokenid``. Previously, the documented format with embedded user in the token ID was not working (https://github.com/ansible-collections/community.proxmox/issues/475).
- proxmox - delegate ``mount_devices[].mode`` validation to the Proxmox API, allowing the API-required four-digit octal format such as ``0666`` (https://github.com/ansible-collections/community.proxmox/issues/533).
- proxmox - do not send ``cmode`` on LXC container update when it is set to the ``default`` sentinel value (PVE rejects the literal value, same as was already handled on instance creation).
- proxmox - fix default value for ``cmode`` parameter (https://github.com/ansible-collections/community.proxmox/pull/440).
- proxmox - omit path parameters from LXC configuration update payloads and serialize tags as a semicolon-separated string, fixing updates with the local backend (https://github.com/ansible-collections/community.proxmox/issues/513).
- proxmox inventory - fetch pool members via the ``GET /pools?poolid=<id>`` query form instead of the deprecated ``GET /pools/{poolid}`` path form, which returned a 501 error and aborted inventory parsing for nested pool IDs (poolid containing a slash, e.g. ``parent/child``) introduced in Proxmox VE 8.1 (https://github.com/ansible-collections/community.proxmox/issues/472).
- proxmox inventory - pass ``verify`` explicitly on HTTP requests so ``validate_certs: false`` is honored when ``REQUESTS_CA_BUNDLE`` is set (regression when only ``session.verify`` was used) (https://github.com/ansible-collections/community.proxmox/pull/491).
- proxmox_ceph_pool - change `target_size_ratio` parameter type from `int` to `float` to match Ceph and Proxmox VE API schema (https://github.com/ansible-collections/community.proxmox/issues/524).
- proxmox_cluster_firewall_security_group - a rule entry with ``iface`` set to an empty string no longer fails to update an existing rule (https://github.com/ansible-collections/community.proxmox/pull/537).
- proxmox_disk module - Ensure proper update handling of disks with an incomplete value set within proxmoxs configuration layer. In particular freshly imported  disks from ESX. (https://github.com/ansible-collections/community.proxmox/pull/531)
- proxmox_domain - ignore immutable fields (``type`` and ``username-claim``) when updating existing realms (https://github.com/ansible-collections/community.proxmox/issues/448).
- proxmox_firewall - fail on ipset entries that combine an IPv4 address with the IPv6 host prefix ``/128`` instead of silently treating them as the plain IPv4 address. Proxmox rejects such entries as well (https://github.com/ansible-collections/community.proxmox/pull/530).
- proxmox_firewall - fix updating a rule when more than one field differs, which queued the rule multiple times and failed (https://github.com/ansible-collections/community.proxmox/pull/493).
- proxmox_firewall - keep the prefix of IPv6 ``/32`` networks such as ``2001:db8::/32`` in ipsets instead of normalizing them to the single address ``2001:db8::/128``. This also fixes ``state=absent`` not removing such a network from an ipset (https://github.com/ansible-collections/community.proxmox/pull/530).
- proxmox_firewall - omit unsupported "pos" API parameter (https://github.com/ansible-collections/community.proxmox/issues/485).
- proxmox_firewall_info - skip aliases and ipsets API calls for firewall for node, vnet and group (https://github.com/ansible-collections/community.proxmox/pull/485).
- proxmox_node_firewall_options - apply ``state=disabled`` on a node whose ``host.fw`` does not set ``enable`` (https://github.com/ansible-collections/community.proxmox/issues/511).
- proxmox_node_firewall_options_info - report ``enabled`` as ``true`` for a node whose ``host.fw`` does not set ``enable`` (https://github.com/ansible-collections/community.proxmox/issues/511).
- proxmox_node_info - skip node ``network`` and ``version`` info when node is offline to prevent errors (https://github.com/ansible-collections/community.proxmox/issues/453).
- proxmox_pct_remote connection plugin - restore the ``_raise_paramiko_connect_exception`` helper that was referenced but not defined after a refactor, so unexpected SSH connection errors (connection refused, timeouts) are reported as ``AnsibleConnectionFailure`` with the real error message instead of crashing with ``AttributeError`` (https://github.com/ansible-collections/community.proxmox/issues/477).
- proxmox_pool_member - fix incorrect type when adding members (https://github.com/ansible-collections/community.proxmox/issues/459).
- proxmox_pool_member - fix support adding and removing in one execution in ``exclusive`` mode (https://github.com/ansible-collections/community.proxmox/pull/467).
- proxmox_qemu_api connection plugin - export ``HOME`` for every command executed through the QEMU guest agent, which starts processes without a login environment. With ``HOME`` unset, POSIX sh left ``~`` unexpanded, breaking ansible-core's remote tmpdir discovery and causing ``copy``, ``template`` and module payload transfers to fail after creating a literal ``/~`` directory on the guest (https://github.com/ansible-collections/community.proxmox/issues/461).
- proxmox_template - fix error if ``api_host`` and upload target `node` are not the same (https://github.com/ansible-collections/community.proxmox/issues/222).
- proxmox_user - allow password change with e.g. local backend (https://github.com/ansible-collections/community.proxmox/issues/482).
- proxmox_user - ignore ``password`` parameter when updating an existing user using API Token authentication (https://github.com/ansible-collections/community.proxmox/issues/451).
- proxmox_user - omit unknown API parameter (https://github.com/ansible-collections/community.proxmox/issues/481).
- proxmox_user - report changed in check mode when deleting user (https://github.com/ansible-collections/community.proxmox/pull/515).
- proxmox_vm_info - ignore errors when retrieving VM network info if the QEMU guest agent is not running (https://github.com/ansible-collections/community.proxmox/pull/507).
- proxmox_vm_info - skip VM network info when VM is stopped (https://github.com/ansible-collections/community.proxmox/pull/504).

New Modules
-----------

- community.proxmox.proxmox_cluster_firewall_security_group - Cluster firewall security group management for Proxmox VE.

v2.0.0
======

Release Summary
---------------

This is the major release of the ``community.proxmox`` collection.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release.

Please note that this version of the collection now requires proxmoxer 2.3.0 or higher.

Minor Changes
-------------

- proxmox - add ``destroy_unreferenced_disks`` parameter (https://github.com/ansible-collections/community.proxmox/pull/422).
- proxmox - add ``totp`` authentification support (https://github.com/ansible-collections/community.proxmox/pull/265).
- proxmox - add a new helper `create_proxmox_module()` which adds generic auth args and constraints, and merges in the module-specific args and options (https://github.com/ansible-collections/community.proxmox/pull/289).
- proxmox - adds ``cmode`` parameter for supporting console modes (https://github.com/ansible-collections/community.proxmox/pull/420  / issue https://github.com/ansible-collections/community.proxmox/issues/65).
- proxmox - update ``proxmoxer`` required dependencies to ``>=2.3`` (https://github.com/ansible-collections/community.proxmox/pull/265).
- proxmox inventory - add ``templates`` group to the inventory (https://github.com/ansible-collections/community.proxmox/pull/399).
- proxmox_acme_account - set ``no_log`` on sensitive value ``eab_kid`` (https://github.com/ansible-collections/community.proxmox/pull/418).
- proxmox_kvm - add ``destroy_unreferenced_disks`` parameter (https://github.com/ansible-collections/community.proxmox/pull/422).
- proxmox_kvm - add qemu parameter ``spice_enhancements`` (https://github.com/ansible-collections/community.proxmox/pull/324).
- proxmox_kvm - add qemu parameter ``virtiofs`` (https://github.com/ansible-collections/community.proxmox/pull/336).
- proxmox_node - add alias ``certificate_file_path`` for ``cert`` (https://github.com/ansible-collections/community.proxmox/pull/331).
- proxmox_node - add alias ``node`` for ``node_name`` (https://github.com/ansible-collections/community.proxmox/pull/331).
- proxmox_node - add alias ``private_key_file_path`` for ``key`` (https://github.com/ansible-collections/community.proxmox/pull/331).
- proxmox_node - add new parameter ``certificate`` to pass raw PEM encoded certificate (https://github.com/ansible-collections/community.proxmox/pull/331).
- proxmox_node - add new parameter ``private_key`` to pass raw PEM encoded private key (https://github.com/ansible-collections/community.proxmox/pull/331).
- proxmox_storage - Add support for RBD (RADOS Block Device) storage (https://github.com/ansible-collections/community.proxmox/issues/329).
- proxmox_storage - add ``preallocation`` parameter on ``cifs`` storage backend (https://github.com/ansible-collections/community.proxmox/pull/386).
- proxmox_storage - add ``preallocation`` parameter on ``nfs`` storage backend (https://github.com/ansible-collections/community.proxmox/pull/390).
- proxmox_storage - add ``snapshot_as_volume_chain`` parameter on ``cifs`` storage backend (https://github.com/ansible-collections/community.proxmox/pull/387).
- proxmox_storage - add alias ``subdirectory`` for ``subdir`` on cifs backend (https://github.com/ansible-collections/community.proxmox/pull/388).
- proxmox_storage - add support of ``encryption_key`` on ``pbs`` storage backend (https://github.com/ansible-collections/community.proxmox/pull/389).
- proxmox_storage - enhanced error handling and parameters validation (https://github.com/ansible-collections/community.proxmox/pull/305).
- proxmox_storage - the parameter ``state`` now has a default value of ``present`` (https://github.com/ansible-collections/community.proxmox/pull/305).
- proxmox_storage - when ``state=present`` parameters ``content`` and ``nodes`` are now not required (https://github.com/ansible-collections/community.proxmox/pull/315).

Breaking Changes / Porting Guide
--------------------------------

- proxmox_pool_member - move `member` parameter to a `members` list to manage multiple pool members at once. Add a new `exclusive` parameter to switch between full and incremental mode (https://github.com/ansible-collections/community.proxmox/pull/373 / issue https://github.com/ansible-collections/community.proxmox/issues/320).

Bugfixes
--------

- proxmox - fix ``tags`` always being reported as changed on LXC container updates because the list value was compared against Proxmox's semicolon-delimited string form (https://github.com/ansible-collections/community.proxmox/pull/415).
- proxmox modules - fix calls to ``get_storages()`` to use the correct keyword argument (https://github.com/ansible-collections/community.proxmox/pull/401).
- proxmox_cluster_firewall - error message for invalid log_ratelimit.rate parameter (https://github.com/ansible-collections/community.proxmox/pull/340).
- proxmox_disk - add support for efidisk and tpmstate disk bus types which previously caused module failure with "Unsupported disk bus" error (https://github.com/ansible-collections/community.proxmox/pull/319).
- proxmox_firewall_info - add none guard on get_ip_sets to prevent crash with ``'NoneType' object has no attribute 'ipset'`` when using ``level=group`` (https://github.com/ansible-collections/community.proxmox/issues/430).
- proxmox_pool - member retrieval (https://github.com/ansible-collections/community.proxmox/pull/412).
- proxmox_pool - support nested pool (https://github.com/ansible-collections/community.proxmox/pull/316).
- proxmox_pool_member - fix pool membership operations failing for nested pool IDs (https://github.com/ansible-collections/community.proxmox/pull/428).
- proxmox_pool_member - fix pool membership update (https://github.com/ansible-collections/community.proxmox/pull/428).
- proxmox_pool_member - fix usage of storage member (https://github.com/ansible-collections/community.proxmox/pull/411).
- proxmox_pool_member - member retrieval (https://github.com/ansible-collections/community.proxmox/pull/412).
- proxmox_snap - fail the task when a given snapname does not exist instead of exiting (https://github.com/ansible-collections/community.proxmox/pull/365).
- proxmox_storage - backend ``cephfs``, ``dir`` and ``zfspool`` doesn't requires ``content`` parameter (https://github.com/ansible-collections/community.proxmox/pull/315).
- proxmox_storage - the parameter ``client_keyring`` was ignored (https://github.com/ansible-collections/community.proxmox/pull/305).
- proxmox_storage - the parameter ``fs_name`` was ignored (https://github.com/ansible-collections/community.proxmox/pull/305).
- proxmox_storage - the parameter ``state`` was optional and without default value (https://github.com/ansible-collections/community.proxmox/pull/305).

New Plugins
-----------

Connection
~~~~~~~~~~

- community.proxmox.proxmox_qemu_api - Connect to QEMU VMs via the Proxmox guest agent API.

New Modules
-----------

- community.proxmox.proxmox_acme_account - Manages an ACME account.
- community.proxmox.proxmox_acme_account_info - Retrieves information about a specific ACME account.
- community.proxmox.proxmox_acme_accounts_info - Retrieves the list of ACME accounts.
- community.proxmox.proxmox_acme_certificate - Manages ACME SSL certificates for Proxmox VE nodes.
- community.proxmox.proxmox_acme_certificates_info - Retrieves the list of certificates on a Proxmox VE node.
- community.proxmox.proxmox_acme_plugin_dns - Manage ACME DNS plugins on a Proxmox VE.
- community.proxmox.proxmox_acme_plugin_info - Retrieves a single ACME plugin.
- community.proxmox.proxmox_acme_plugins_info - Retrieves the list of ACME plugins.
- community.proxmox.proxmox_ceph_pool - Manage Ceph Pool.
- community.proxmox.proxmox_cluster_ha_rules_info - Retrieve Proxmox VE HA rules.
- community.proxmox.proxmox_domain - Manage authentication realms.
- community.proxmox.proxmox_domain_sync - Sync realms.

v1.6.0
======

Release Summary
---------------

This is the minor release of the ``community.proxmox`` collection.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release.

Major Changes
-------------

- proxmox - Add ca_path option to specify a ca-certificate for tls validation (https://github.com/ansible-collections/community.proxmox/pull/256).

Minor Changes
-------------

- inventory plugin - add want_post_filtering_facts to delay fact gathering until filtering has completed (https://github.com/ansible-collections/community.proxmox/pull/261).
- proxmox - Add api_timeout option for all modules (https://github.com/ansible-collections/community.proxmox/pull/253).
- proxmox - set ``state`` as not ``required`` and set default value ``present`` (https://github.com/ansible-collections/community.proxmox/pull/292).
- proxmox_role - add role's privs on the return data (https://github.com/ansible-collections/community.proxmox/pull/283).
- proxmox_storage - Add support for ZFS thin-provisioning (https://github.com/ansible-collections/community.proxmox/pull/265).
- proxmox_storage - Add the option namespace for PBS storage (https://github.com/ansible-collections/community.proxmox/pull/282)
- proxmox_storage - refactor the validation of storage options (https://github.com/ansible-collections/community.proxmox/pull/266).
- proxmox_storage_contents_info - Add support for content type ``import`` (https://github.com/ansible-collections/community.proxmox/pull/260).
- proxmox_zone, proxmox_vnet, proxmox_subnet - make sdn modules compatible with pve8 (https://github.com/ansible-collections/community.proxmox/pull/254).

Deprecated Features
-------------------

- proxmox - Certificate verification default changes from ``false`` to ``true`` with version 2.0.0 (https://github.com/ansible-collections/community.proxmox/pull/256).

Bugfixes
--------

- proxmox_cluster - make cluster join idempotent (https://github.com/ansible-collections/community.proxmox/pull/244).
- proxmox_disk - make none iso disk idempotent (https://github.com/ansible-collections/community.proxmox/pull/288).
- proxmox_firewall - Enable ipsets on vm level and fix bugs regarding the cidr notation the proxmox api expects (https://github.com/ansible-collections/community.proxmox/pull/248).
- proxmox_role - when privs is omitted, keep existing role privileges unchanged instead of treating it as no privileges (https://github.com/ansible-collections/community.proxmox/pull/284).

New Modules
-----------

- community.proxmox.proxmox_role - Role management for Proxmox VE cluster.

v1.5.0
======

Release Summary
---------------

This is the minor release of the ``community.proxmox`` collection.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release.

Minor Changes
-------------

- inventory plugin, plugin_utils - replace deprecated ``ansible.module_utils.common._collections_compat`` imports with ``collections.abc`` from the Python standard library (https://github.com/ansible-collections/community.proxmox/issues/241).
- proxmox - change disk size units to GiB (https://github.com/ansible-collections/community.proxmox/pull/236).
- proxmox_disk - change disk size units to GiB (https://github.com/ansible-collections/community.proxmox/pull/236).
- proxmox_kvm - add option to migrate local disks as well (https://github.com/ansible-collections/community.proxmox/pull/240).
- proxmox_kvm - change disk size units to GiB (https://github.com/ansible-collections/community.proxmox/pull/236).
- proxmox_node_info - add information on node network interfaces to node information output (https://github.com/ansible-collections/community.proxmox/pull/220).
- proxmox_node_info - add information on node's PVE version (https://github.com/ansible-collections/community.proxmox/pull/225).
- proxmox_snap_info - Adds a new module to list snapshots or a specific snapshot for VM or container (https://github.com/ansible-collections/community.proxmox/issues/229).
- proxmox_storage - add feature of subdirectory in CIFS share. (https://github.com/ansible-collections/community.proxmox/pull/214).
- proxmox_storage - fix passing nfs_options to API payload (https://github.com/ansible-collections/community.proxmox/issues/203, https://github.com/ansible-collections/community.proxmox/pull/221).
- proxmox_storage - fixed CIFS authentication by sending username and password parameters to proxmoxer (https://github.com/ansible-collections/community.proxmox/pull/214).

Bugfixes
--------

- proxmox all - add missing timeout parameter to proxmoxer object creation (https://github.com/ansible-collections/community.proxmox/pull/218).
- proxmox_ipam_info - fix bug where selecting by vmid did not work (https://github.com/ansible-collections/community.proxmox/pull/211).
- proxmox_zone - fix validation logic for VXLAN zones to accept either ``fabric`` or ``peers`` parameter. Previously, only ``fabric`` was accepted, but Proxmox VE also supports creating VXLAN zones with a peer address list (https://github.com/ansible-collections/community.proxmox/issues/216).
- remove wrong api endpoints and error messages from proxmod_node certificate management(https://github.com/ansible-collections/community.proxmox/pull/232).

New Modules
-----------

- community.proxmox.proxmox_ceph_mds - Add or delete Ceph Mds.
- community.proxmox.proxmox_ceph_mgr - Add or delete Ceph Manager.
- community.proxmox.proxmox_ceph_mon - Add or delete Ceph Monitor.
- community.proxmox.proxmox_sendkey - Send key presses to a Proxmox VM console.

v1.4.0
======

Release Summary
---------------

This is the minor release of the ``community.proxmox`` collection.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release.

Minor Changes
-------------

- proxmox - Add delete parameter to delete settings (https://github.com/ansible-collections/community.proxmox/pull/195).
- proxmox_cluster -  Add master_api_password for authentication against master node (https://github.com/ansible-collections/community.proxmox/pull/140).
- proxmox_cluster - added link0 and link1 to join command (https://github.com/ansible-collections/community.proxmox/issues/168, https://github.com/ansible-collections/community.proxmox/pull/172).
- proxmox_kvm - update description of machine parameter in proxmox_kvm.py (https://github.com/ansible-collections/community.proxmox/pull/186)
- proxmox_storage - added `dir` and `zfspool` storage types (https://github.com/ansible-collections/community.proxmox/pull/184)
- proxmox_tasks_info - add source option to specify tasks to consider (https://github.com/ansible-collections/community.proxmox/pull/179)
- proxmox_template -  Add 'import' to allowed content types of proxmox_template, so disk images and can be used as disk images on VM creation (https://github.com/ansible-collections/community.proxmox/pull/162).

Bugfixes
--------

- proxmox inventory plugin and proxmox module utils - avoid Python 2 compatibility imports (https://github.com/ansible-collections/community.proxmox/pull/175).
- proxmox_kvm - remove limited choice for vga option in proxmox_kvm (https://github.com/ansible-collections/community.proxmox/pull/185)
- proxmox_kvm, proxmox_template - remove ``ansible.module_utils.six`` dependency (https://github.com/ansible-collections/community.proxmox/pull/201).
- proxmox_storage - fixed adding PBS-type storage by ensuring its parameters (server, datastore, etc.) are correctly sent to the Proxmox API (https://github.com/ansible-collections/community.proxmox/pull/171).
- proxmox_user - added a third case when testing for not-yet-existant user (https://github.com/ansible-collections/community.proxmox/issues/163)
- proxmox_vm_info - do not throw exception when iterating through machines and optional api results are missing (https://github.com/ansible-collections/community.proxmox/pull/191)

New Modules
-----------

- community.proxmox.proxmox_cluster_ha_rules - Management of HA rules.
- community.proxmox.proxmox_firewall - Manage firewall rules in Proxmox.
- community.proxmox.proxmox_firewall_info - Manage firewall rules in Proxmox.
- community.proxmox.proxmox_ipam_info - Retrieve information about IPAMs.
- community.proxmox.proxmox_subnet - Create/Update/Delete subnets from SDN.
- community.proxmox.proxmox_vnet - Manage virtual networks in Proxmox SDN.
- community.proxmox.proxmox_vnet_info - Retrieve information about one or more Proxmox VE SDN vnets.
- community.proxmox.proxmox_zone - Manage Proxmox zone configurations.
- community.proxmox.proxmox_zone_info - Get Proxmox zone info.

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

- community.proxmox.proxmox_access_acl - Manages ACLs on the Proxmox PVE cluster.
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
