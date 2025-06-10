# Community Proxmox Collection Release Notes

**Topics**

- <a href="#v1-0-1">v1\.0\.1</a>
    - <a href="#release-summary">Release Summary</a>
    - <a href="#minor-changes">Minor Changes</a>
- <a href="#v1-0-0">v1\.0\.0</a>
    - <a href="#release-summary-1">Release Summary</a>
    - <a href="#minor-changes-1">Minor Changes</a>
    - <a href="#breaking-changes--porting-guide">Breaking Changes / Porting Guide</a>
    - <a href="#bugfixes">Bugfixes</a>
    - <a href="#new-modules">New Modules</a>
- <a href="#v0-1-0">v0\.1\.0</a>
    - <a href="#release-summary-2">Release Summary</a>

<a id="v1-0-1"></a>
## v1\.0\.1

<a id="release-summary"></a>
### Release Summary

This is a minor bugfix release for the <code>community\.proxmox</code> collections\.
This changelog contains all changes to the modules and plugins in this collection
that have been made after the previous release\.

<a id="minor-changes"></a>
### Minor Changes

* proxmox module utils \- fix handling warnings in LXC tasks \([https\://github\.com/ansible\-collections/community\.proxmox/pull/104](https\://github\.com/ansible\-collections/community\.proxmox/pull/104)\)\.

<a id="v1-0-0"></a>
## v1\.0\.0

<a id="release-summary-1"></a>
### Release Summary

This is the first stable release of the <code>community\.proxmox</code> collection since moving from <code>community\.general</code>\, released on 2025\-06\-08\.

<a id="minor-changes-1"></a>
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

<a id="bugfixes"></a>
### Bugfixes

* proxmox \- fix crash in module when the used on an existing LXC container with <code>state\=present</code> and <code>force\=true</code> \([https\://github\.com/ansible\-collections/community\.proxmox/pull/91](https\://github\.com/ansible\-collections/community\.proxmox/pull/91)\)\.

<a id="new-modules"></a>
### New Modules

* community\.proxmox\.proxmox\_backup\_schedule \- Schedule VM backups and removing them\.
* community\.proxmox\.proxmox\_cluster \- Create and join Proxmox VE clusters\.
* community\.proxmox\.proxmox\_cluster\_join\_info \- Retrieve the join information of the Proxmox VE cluster\.

<a id="v0-1-0"></a>
## v0\.1\.0

<a id="release-summary-2"></a>
### Release Summary

This is the first community\.proxmox release\. It contains mainly the state of the Proxmox content in community\.general 10\.6\.0\.
The minimum required ansible\-core version for community\.proxmox is ansible\-core 2\.17\, which implies Python 3\.7\+\.
The minimum required proxmoxer version is 2\.0\.0\.
