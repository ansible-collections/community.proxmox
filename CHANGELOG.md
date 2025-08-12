# Community Proxmox Collection Release Notes

**Topics**

- <a href="#v1-3-0">v1\.3\.0</a>
    - <a href="#release-summary">Release Summary</a>
    - <a href="#minor-changes">Minor Changes</a>
    - <a href="#bugfixes">Bugfixes</a>
    - <a href="#new-modules">New Modules</a>
- <a href="#v1-2-0">v1\.2\.0</a>
    - <a href="#release-summary-1">Release Summary</a>
    - <a href="#minor-changes-1">Minor Changes</a>
    - <a href="#new-modules-1">New Modules</a>
- <a href="#v1-1-0">v1\.1\.0</a>
    - <a href="#release-summary-2">Release Summary</a>
    - <a href="#minor-changes-2">Minor Changes</a>
    - <a href="#bugfixes-1">Bugfixes</a>
    - <a href="#new-modules-2">New Modules</a>
- <a href="#v1-0-1">v1\.0\.1</a>
    - <a href="#release-summary-3">Release Summary</a>
    - <a href="#minor-changes-3">Minor Changes</a>
- <a href="#v1-0-0">v1\.0\.0</a>
    - <a href="#release-summary-4">Release Summary</a>
    - <a href="#minor-changes-4">Minor Changes</a>
    - <a href="#breaking-changes--porting-guide">Breaking Changes / Porting Guide</a>
    - <a href="#bugfixes-2">Bugfixes</a>
    - <a href="#new-modules-3">New Modules</a>
- <a href="#v0-1-0">v0\.1\.0</a>
    - <a href="#release-summary-5">Release Summary</a>

<a id="v1-3-0"></a>
## v1\.3\.0

<a id="release-summary"></a>
### Release Summary

This is the minor release of the <code>community\.proxmox</code> collection\.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release\.

<a id="minor-changes"></a>
### Minor Changes

* proxmox\* modules \- added fallback environment variables for <code>api\_token</code>\, <code>api\_secret</code>\, and <code>validate\_certs</code> \([https\://github\.com/ansible\-collections/community\.proxmox/issues/63](https\://github\.com/ansible\-collections/community\.proxmox/issues/63)\, [https\://github\.com/ansible\-collections/community\.proxmox/pull/136](https\://github\.com/ansible\-collections/community\.proxmox/pull/136)\)\.
* proxmox\_cluster\_ha\_groups \- fix idempotency in proxmox\_cluster\_ha\_groups module \([https\://github\.com/ansible\-collections/community\.proxmox/issues/138](https\://github\.com/ansible\-collections/community\.proxmox/issues/138)\, [https\://github\.com/ansible\-collections/community\.proxmox/pull/139](https\://github\.com/ansible\-collections/community\.proxmox/pull/139)\)\.
* proxmox\_cluster\_ha\_resources \-  Fix idempotency proxmox\_cluster\_ha\_resources \([https\://github\.com/ansible\-collections/community\.proxmox/pull/135](https\://github\.com/ansible\-collections/community\.proxmox/pull/135)\)\.
* proxmox\_kvm \- Add missing \'storage\' parameter to create\_vm\(\)\-call\.
* proxmox\_kvm \- add new purge parameter to proxmox\_kvm module \([https\://github\.com/ansible\-collections/community\.proxmox/issues/60](https\://github\.com/ansible\-collections/community\.proxmox/issues/60)\, [https\://github\.com/ansible\-collections/community\.proxmox/pull/148](https\://github\.com/ansible\-collections/community\.proxmox/pull/148)\)\.

<a id="bugfixes"></a>
### Bugfixes

* proxmox\_pct\_remote connection plugin \- avoid deprecated ansible\-core paramiko import helper\, import paramiko directly instead \([https\://github\.com/ansible\-collections/community\.proxmox/issues/146](https\://github\.com/ansible\-collections/community\.proxmox/issues/146)\, [https\://github\.com/ansible\-collections/community\.proxmox/pull/151](https\://github\.com/ansible\-collections/community\.proxmox/pull/151)\)\.

<a id="new-modules"></a>
### New Modules

* community\.proxmox\.proxmox\_storage \- Manage storage in PVE clusters and nodes\.

<a id="v1-2-0"></a>
## v1\.2\.0

<a id="release-summary-1"></a>
### Release Summary

This is the minor release of the <code>community\.proxmox</code> collection\.
This changelog contains all changes to the modules and plugins in this collection that have been made after the previous release\.

<a id="minor-changes-1"></a>
### Minor Changes

* proxmox inventory plugin \- always provide basic information regardless of want\_facts \([https\://github\.com/ansible\-collections/community\.proxmox/pull/124](https\://github\.com/ansible\-collections/community\.proxmox/pull/124)\)\.
* proxmox\_cluster \- cluster creation has been made idempotent \([https\://github\.com/ansible\-collections/community\.proxmox/pull/125](https\://github\.com/ansible\-collections/community\.proxmox/pull/125)\)\.
* proxmox\_pct\_remote \- allow forward agent with paramiko \([https\://github\.com/ansible\-collections/community\.proxmox/pull/130](https\://github\.com/ansible\-collections/community\.proxmox/pull/130)\)\.

<a id="new-modules-1"></a>
### New Modules

* community\.proxmox\.proxmox\_group \- Group management for Proxmox VE cluster\.
* community\.proxmox\.proxmox\_node \- Manage Proxmox VE nodes\.
* community\.proxmox\.proxmox\_user \- User management for Proxmox VE cluster\.

<a id="v1-1-0"></a>
## v1\.1\.0

<a id="release-summary-2"></a>
### Release Summary

This is the minor release of the <code>community\.proxmox</code> collection\.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release\.

<a id="minor-changes-2"></a>
### Minor Changes

* proxmox \- allow force deletion of LXC containers \([https\://github\.com/ansible\-collections/community\.proxmox/pull/105](https\://github\.com/ansible\-collections/community\.proxmox/pull/105)\)\.
* proxmox \- validate the cluster name length \([https\://github\.com/ansible\-collections/community\.proxmox/pull/119](https\://github\.com/ansible\-collections/community\.proxmox/pull/119)\)\.

<a id="bugfixes-1"></a>
### Bugfixes

* proxmox inventory plugin \- avoid using deprecated option when templating options \([https\://github\.com/ansible\-collections/community\.proxmox/pull/108](https\://github\.com/ansible\-collections/community\.proxmox/pull/108)\)\.

<a id="new-modules-2"></a>
### New Modules

* community\.proxmox\.proxmox\_access\_acl \- Management of ACLs for objects in Proxmox VE Cluster\.
* community\.proxmox\.proxmox\_cluster\_ha\_groups \- Management of HA groups in Proxmox VE Cluster\.
* community\.proxmox\.proxmox\_cluster\_ha\_resources \- Management of HA groups in Proxmox VE Cluster\.

<a id="v1-0-1"></a>
## v1\.0\.1

<a id="release-summary-3"></a>
### Release Summary

This is a minor bugfix release for the <code>community\.proxmox</code> collections\.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release\.

<a id="minor-changes-3"></a>
### Minor Changes

* proxmox module utils \- fix handling warnings in LXC tasks \([https\://github\.com/ansible\-collections/community\.proxmox/pull/104](https\://github\.com/ansible\-collections/community\.proxmox/pull/104)\)\.

<a id="v1-0-0"></a>
## v1\.0\.0

<a id="release-summary-4"></a>
### Release Summary

This is the first stable release of the <code>community\.proxmox</code> collection since moving from <code>community\.general</code>\, released on 2025\-06\-08\.

<a id="minor-changes-4"></a>
### Minor Changes

* proxmox \- add support for creating and updating containers in the same task \([https\://github\.com/ansible\-collections/community\.proxmox/pull/92](https\://github\.com/ansible\-collections/community\.proxmox/pull/92)\)\.
* proxmox module util \- do not hang on tasks that throw warnings \([https\://github\.com/ansible\-collections/community\.proxmox/issues/96](https\://github\.com/ansible\-collections/community\.proxmox/issues/96)\, [https\://github\.com/ansible\-collections/community\.proxmox/pull/100](https\://github\.com/ansible\-collections/community\.proxmox/pull/100)\)\.
* proxmox\_kvm \- add <code>rng0</code> option to specify an RNG device \([https\://github\.com/ansible\-collections/community\.proxmox/pull/18](https\://github\.com/ansible\-collections/community\.proxmox/pull/18)\)\.
* proxmox\_kvm \- remove redundant check for duplicate names as this is allowed by PVE API \([https\://github\.com/ansible\-collections/community\.proxmox/issues/97](https\://github\.com/ansible\-collections/community\.proxmox/issues/97)\, [https\://github\.com/ansible\-collections/community\.proxmox/pull/99](https\://github\.com/ansible\-collections/community\.proxmox/pull/99)\)\.
* proxmox\_snap \- correctly handle proxmox\_snap timeout parameter \([https\://github\.com/ansible\-collections/community\.proxmox/issues/73](https\://github\.com/ansible\-collections/community\.proxmox/issues/73)\, [https\://github\.com/ansible\-collections/community\.proxmox/issues/95](https\://github\.com/ansible\-collections/community\.proxmox/issues/95)\, [https\://github\.com/ansible\-collections/community\.proxmox/pull/101](https\://github\.com/ansible\-collections/community\.proxmox/pull/101)\)\.

<a id="breaking-changes--porting-guide"></a>
### Breaking Changes / Porting Guide

* proxmox \- <code>update</code> and <code>force</code> are now mutually exclusive \([https\://github\.com/ansible\-collections/community\.proxmox/pull/92](https\://github\.com/ansible\-collections/community\.proxmox/pull/92)\)\.
* proxmox \- the default of <code>update</code> changed from <code>false</code> to <code>true</code> \([https\://github\.com/ansible\-collections/community\.proxmox/pull/92](https\://github\.com/ansible\-collections/community\.proxmox/pull/92)\)\.

<a id="bugfixes-2"></a>
### Bugfixes

* proxmox \- fix crash in module when the used on an existing LXC container with <code>state\=present</code> and <code>force\=true</code> \([https\://github\.com/ansible\-collections/community\.proxmox/pull/91](https\://github\.com/ansible\-collections/community\.proxmox/pull/91)\)\.

<a id="new-modules-3"></a>
### New Modules

* community\.proxmox\.proxmox\_backup\_schedule \- Schedule VM backups and removing them\.
* community\.proxmox\.proxmox\_cluster \- Create and join Proxmox VE clusters\.
* community\.proxmox\.proxmox\_cluster\_join\_info \- Retrieve the join information of the Proxmox VE cluster\.

<a id="v0-1-0"></a>
## v0\.1\.0

<a id="release-summary-5"></a>
### Release Summary

This is the first community\.proxmox release\. It contains mainly the state of the Proxmox content in community\.general 10\.6\.0\.
The minimum required ansible\-core version for community\.proxmox is ansible\-core 2\.17\, which implies Python 3\.7\+\.
The minimum required proxmoxer version is 2\.0\.0\.
