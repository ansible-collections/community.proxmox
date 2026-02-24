<!--
Copyright (c) Ansible Project
GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Contributing

We follow [Ansible Code of Conduct](https://docs.ansible.com/projects/ansible/latest/community/code_of_conduct.html) 
in all our contributions and interactions within this repository. If you are stuck while developing a
module, refer to our [recommended reads](#helpful-documentation) from the Ansible docs.

## Issue tracker

Whether you are looking for an opportunity to contribute or you found a bug and already know how to 
solve it, please go to the [issue tracker](https://github.com/ansible-collections/community.proxmox/issues).
There you can find feature ideas to implement, reports about bugs to solve, or submit an issue to 
discuss your idea before implementing it which can help choose a right direction at the beginning of 
your work and potentially save a lot of time and effort.
Also somebody may already have started discussing or working on implementing the same or a similar idea,
so you can cooperate to create a better solution together.
<!-- We currently do not maintain these tags
* If you are interested in starting with an easy issue, look for [issues with an `easyfix` label](https://github.com/ansible-collections/community.proxmox/labels/easyfix).
* Often issues that are waiting for contributors to pick up have [the `waiting_on_contributor` label](https://github.com/ansible-collections/community.proxmox/labels/waiting_on_contributor).
-->

## Review pull requests

Look through currently [open pull requests](https://github.com/ansible-collections/community.proxmox/pulls).

You can help by reviewing and testing them, since this collection currently lacks integration tests. 
Reviews and tests help us estimate the maturity of a pull request and increase the likelihood to merge its contents. 
Note that reviewing does not only mean code review, but also offering comments on new interfaces added to existing plugins/modules, 
interfaces of new plugins/modules, improving language (not everyone is a native English speaker), or testing bugfixes and new features!

Also, consider taking up a valuable, reviewed, but abandoned pull request which you could politely ask the original authors to complete yourself.

If you want to test a PR locally, refer to [our testing guide](https://docs.ansible.com/projects/ansible/devel/community/collection_contributors/collection_test_pr_locally.html) for instructions on how do it quickly.

If you find any inconsistencies or places in this document which can be improved, feel free to raise an issue or pull request to fix it.

## Opening pull requests
Wether you found a bug and want to fix it or you want to contribute a new module, 
please refer to these conventions:
* Try committing your changes with an informative but short commit message.
* Make sure your PR includes a [changelog fragment](https://docs.ansible.com/projects/ansible/devel/community/collection_development_process.html#creating-a-changelog-fragment).
  * You must not include a fragment for new modules or new plugins. Also you shouldn't include one for docs-only changes.
  * Please always include a link to the pull request itself, and if the PR is about an issue, also a link to the issue. Also make sure the fragment ends with a period, and begins with a lower-case letter after `-`. (Again, if you don't do this, we'll add suggestions to fix it, so don't worry too much :) )
* Note that we lint and format the code with `ruff`. 
  If your change does not match the expectations, CI will fail and your PR will not get merged. 
  Continue reading this guide to find out how to lint and format your code.

You can also read the Ansible community's [Quick-start development guide](https://docs.ansible.com/projects/ansible/devel/community/create_pr_quick_start.html).

### New modules or plugins

Creating new modules and plugins requires a bit more work than other Pull Requests.

1. Please make sure that your new module or plugin is not already part of this collection. 
   If it is already partly adressed, you might want to add the functionality there or discuss refactoring the functions in an issue.

2. Please do not add more than one plugin/module in one PR, unless they are closely releated. 
   That makes it easier for reviewers, and increases the chance that your PR will get merged. If you plan to contribute a group
   of plugins/modules (say, more than a module and a corresponding `_info` module), please mention that in the first PR.

3. When creating a new module or plugin, please make sure that you follow various guidelines:

   - Follow [development conventions](https://docs.ansible.com/projects/ansible/devel/dev_guide/developing_modules_best_practices.html);
   - Follow [documentation standards](https://docs.ansible.com/projects/ansible/devel/dev_guide/developing_modules_documenting.html) and
     the [Ansible style guide](https://docs.ansible.com/projects/ansible/devel/dev_guide/style_guide/index.html#style-guide);
   - Make sure your modules and plugins are [GPL-3.0-or-later](https://www.gnu.org/licenses/gpl-3.0-standalone.html) licensed
     (new module_utils can also be [BSD-2-clause](https://opensource.org/licenses/BSD-2-Clause) licensed);
   - Make sure that new plugins and modules have unit tests.

## Formatting, linting and tests
We use `ruff` to maintain a baseline of code readability and quality. 
Please check out our [ruff configuration](./ruff.toml) to find out which formatting and rules are enforced.

To perform basic testing, you will most likely require the following packages:
- `antsibull-nox`
- `nox`
- `ruff`
- `ansible`

and ideally a container runtime, for example `podman` or `docker`.    

To immediately run all default tests (format, lint), install the dependencies
and run `nox`. To run all unit/sanity tests, use `nox -s ansible-test-units` or `nox -s ansible-test-sanity`.

### Codequality

The following commands show how to lint and format your code with nox:

```.bash
# Run all configured formatters:
nox -Re formatters

# Lint:
nox -Re codeqa

# If you notice discrepancies between your local formatter and CI, you might
# need to re-generate the virtual environment:
nox -e formatters
```

While antsibull-nox and nox enable you to run the whole suite of tests, you may 
use `ruff format` and `ruff check` immediately within your development environment to perform basic linting and formatting.
Note that while our CI is aware of changed files, your environment may not be. Thus, ruff errors,
which might stem for other files, will not fail the tests of your contribution and can be ignored.

### Sanity tests

The following commands show how to run ansible-test sanity tests:

```.bash
# Run basic sanity tests for all files in the collection:
nox -Re ansible-test-sanity-devel

# Run basic sanity tests for the given files and directories:
nox -Re ansible-test-sanity-devel -- plugins/modules/system/pids.py tests/integration/targets/pids/

# Run all other sanity tests for all files in the collection:
nox -R
```

### Unit tests

The following commands show how to run unit tests:

```.bash
# Run all unit tests:
nox -Re ansible-test-units-devel

# Run all unit tests for one Python version (a lot faster):
nox -Re ansible-test-units-devel -- --python 3.13

# Run a specific unit test for one Python version:
nox -Re ansible-test-units-devel -- --python 3.13 tests/unit/plugins/modules/test_proxmox_kvm.py
```

### Manual test and review of changes
If you want to test your new module or bugfix within a playbook, you may do the following:
- Ensure your repository resides, for example, in `exampledir/community/proxmox`.
- Set up Ansible to find your collection `export ANSIBLE_COLLECTIONS_PATH="$HOME/exampledir"`.
  Alternatively, you may edit your [ansible.cfg](https://docs.ansible.com/projects/ansible/latest/reference_appendices/config.html#collections-paths).
- Verify, that your modified collection is found: `ansible-galaxy collection list`

Now you can use your custom code in playbooks and roles. 
And you can use `ansible-doc` to review your rendered documentation.



## Helpful Documentation
Unless you already read it up above, you probably really shoudl check out these links:
- Development:
  - [Module architecture](https://docs.ansible.com/projects/ansible/latest/dev_guide/developing_program_flow_modules.html) (also contains the module options).
  - [Best practises](https://docs.ansible.com/projects/ansible/devel/dev_guide/developing_modules_best_practices.html).
  - [Creating changelog fragments](https://docs.ansible.com/projects/ansible/devel/community/collection_development_process.html#creating-a-changelog-fragment).
- Documentation
  - [Ansible Module parts and blocks](https://docs.ansible.com/projects/ansible/devel/dev_guide/developing_modules_documenting.html).
  - [Style Guide](https://docs.ansible.com/projects/ansible/devel/dev_guide/style_guide/index.html#style-guide), and the subsequent
    [voice style](https://docs.ansible.com/projects/ansible/devel/dev_guide/style_guide/voice_style.html), [grammar](https://docs.ansible.com/projects/ansible/devel/dev_guide/style_guide/grammar_punctuation.html)
    and [spelling](https://docs.ansible.com/projects/ansible/devel/dev_guide/style_guide/spelling_word_choice.html).
  - [Ansible Markup for documentation yaml](https://docs.ansible.com/projects/ansible/latest/dev_guide/ansible_markup.html).
<!-- Omitted for the sake of brevity and kept for historical reasons
## Run basic sanity, unit or integration tests locally (with ansible-test)

Instead of using antsibull-nox, you can also run sanity and unit tests with ansible-test directly.

You have to check out the repository into a specific path structure to be able to run `ansible-test`. 
The path to the git checkout must end with `.../ansible_collections/community/general`. 
Please see [our testing guide](https://docs.ansible.com/projects/ansible/devel/community/collection_contributors/collection_test_pr_locally.html) 
for instructions on how to check out the repository into a correct path structure. The short version of these instructions is:

```.bash
mkdir -p ~/dev/ansible_collections/community
git clone https://github.com/ansible-collections/community.proxmox.git ~/dev/ansible_collections/community/proxmox
cd ~/dev/ansible_collections/community/proxmox
```

Then you can run `ansible-test` (which is a part of [ansible-core](https://pypi.org/project/ansible-core/)) inside the checkout. 
The following example commands expect that you have installed Docker or Podman. 
Note that Podman has only been supported by more recent ansible-core releases. 
If you are using Docker, the following will work with Ansible 2.9+.

### Basic sanity tests

The following commands show how to run basic sanity tests:

```.bash
# Run basic sanity tests for all files in the collection:
ansible-test sanity --docker -v

# Run basic sanity tests for the given files and directories:
ansible-test sanity --docker -v plugins/modules/system/pids.py tests/integration/targets/pids/
```

### Unit tests

Note that for running unit tests, you need to install required collections in the same folder structure that `community.proxmox` is checked out in.
Right now, you need to install [`community.internal_test_tools`](https://github.com/ansible-collections/community.internal_test_tools).
If you want to use the latest version from GitHub, you can run:

```
git clone https://github.com/ansible-collections/community.internal_test_tools.git ~/dev/ansible_collections/community/internal_test_tools
```

The following commands show how to run unit tests:

```.bash
# Run all unit tests:
ansible-test units --docker -v

# Run all unit tests for one Python version (a lot faster):
ansible-test units --docker -v --python 3.8

# Run a specific unit test (for the nmcli module) for one Python version:
ansible-test units --docker -v --python 3.8 tests/unit/plugins/modules/net_tools/test_nmcli.py
```
-->

<!-- todo
## Devcontainer

Since community.general 12.2.0, the project repository supports [devcontainers](https://containers.dev/). In short, it is a standard mechanism to
create a container that is then used during the development cycle. Many tools are pre-installed in the container and will be already available
to you as a developer. A number of different IDEs support that configuration, the most prominent ones being VSCode and PyCharm.

See the files under [.devcontainer](.devcontainer) for details on what is deployed inside that container.

Beware of:

- By default, the devcontainer installs the latest version of `ansible-core`.
  When testing your changes locally, keep in mind that the collection must support older versions of
  `ansible-core` and, depending on what is being tested, results may vary.
- Integration tests executed directly inside the devcontainer without isolation (see above) may fail if
  they expected to be run in full fledged VMs. On the other hand, the devcontainer setup allows running
  containers inside the container (the `docker-in-docker` feature).
- The devcontainer is built with a directory structure such that
  `.../ansible_collections/community/general` contains the project repository, so `ansible-test` and
  other standard tools should work without any additional setup
- By default, the devcontainer installs `pre-commit` and configures it to perform `ruff check` and
  `ruff format` on the Python files, prior to commiting. That configuration is going to be used by
  `git` even outside the devcontainer. To prevent errors, you have to either install `pre-commit` in
  your computer, outside the devcontainer, or run `pre-commit uninstall` from within the devcontainer
  before quitting it.
-->
