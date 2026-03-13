..
  Copyright (c) Ansible Project
  GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
  SPDX-License-Identifier: GPL-3.0-or-later

.. _ansible_collections.community.proxmox.docsite.authentication:

Authentication
================

Modules in this collection need to authenticate to the Proxmox Virtual Environment API.

This collection supports two authentication methods:

- **API token**: recommended for production (scoped and revocable)
- **Username/password**: simplest, good for development and testing

Avoid hard-coding credentials in playbooks or inventory. Prefer Ansible Vault, environment variables, or a secrets manager.

..  note::
    Some operations are not supported with API token authentication (e.g container bind-mounts configuration).

Minimal Example
---------------

Examples below show authentication variables as you would typically define them in group/host vars, role defaults, or play vars.

**API Token**

.. code-block:: yaml

   api_host: 10.0.0.1
   api_token_id: username@realm!tokenid
   api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

**Username/password**

.. code-block:: yaml

   api_host: 10.0.0.1
   api_user: username@realm
   api_password: a-strong-password

Example Playbook Task
---------------------

Most modules in this collection accept the same authentication parameters. A common pattern is to define them once at play level and reuse them across tasks:

.. code-block:: yaml

   - name: Query VMs on Proxmox VE
     hosts: localhost
     gather_facts: false
     vars:
       api_host: 10.0.0.1
       api_token_id: "{{ vault_proxmox_token_id }}"
       api_token_secret: "{{ vault_proxmox_token_secret }}"
       validate_certs: true
     tasks:
       - name: Get VM inventory
         community.proxmox.proxmox_vm_info:
           api_host: "{{ api_host }}"
           api_token_id: "{{ api_token_id }}"
           api_token_secret: "{{ api_token_secret }}"
           validate_certs: "{{ validate_certs }}"

Optional Parameters
-------------------

Here are optional configuration parameters:

.. code-block:: yaml

   api_port: 8006
   api_timeout: 5
   validate_certs: true
   ca_path: ./verify-tls-connection-with-this-authority.pem

Environment Variables
---------------------

Credentials can also be provided via environment variables.

.. list-table::
   :header-rows: 1
   :widths: 22 35

   * - Parameter
     - Environment variable
   * - ``api_host``
     - ``PROXMOX_HOST``
   * - ``api_user``
     - ``PROXMOX_USER``
   * - ``api_password``
     - ``PROXMOX_PASSWORD``
   * - ``api_token_id``
     - ``PROXMOX_TOKEN_ID``
   * - ``api_token_secret``
     - ``PROXMOX_TOKEN_SECRET``
   * - ``validate_certs``
     - ``PROXMOX_VALIDATE_CERTS``

Parameters Reference
--------------------

The following parameters can be used for authentication:

- ``api_host``: Proxmox VE API hostname or IP (can also be sourced from ``PROXMOX_HOST``). Do not include ``https://``, ``:8006`` or ``/api2/json``.
- ``api_port``: Proxmox VE API port (default: 8006).
- ``api_user``: Username and realm (can also be sourced from ``PROXMOX_USER``). For example, ``root@pam``.
- ``api_password``: Password (can also be sourced from ``PROXMOX_PASSWORD``).
- ``api_token_id``: Token identifier in the form ``username@realm!tokenid`` (can also be sourced from ``PROXMOX_TOKEN_ID``).
- ``api_token_secret``: Token secret (can also be sourced from ``PROXMOX_TOKEN_SECRET``).
- ``validate_certs``: Validate TLS certificates (can also be sourced from ``PROXMOX_VALIDATE_CERTS``). Defaults to false prior v2.0.0.
- ``ca_path``: Path to a CA certificate file used to validate the Proxmox VE TLS certificate.
- ``api_timeout``: Request timeout in seconds. Defaults to 5 seconds.
