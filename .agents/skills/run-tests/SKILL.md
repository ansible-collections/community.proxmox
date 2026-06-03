<!--
Copyright (c) Ansible Project
GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
SPDX-License-Identifier: GPL-3.0-or-later
-->

---
name: run-tests
description: Runs and writes tests (sanity, unit, integration) for the community.proxmox Ansible collection using ansible-test. Use when asked to run, check, or write tests for a module or utility. Do not use for PR reviews or questions unrelated to testing.
---

# Skill: run-tests

## Purpose

Run and write tests for the `community.proxmox` Ansible collection. Covers sanity, unit, and integration tests using `ansible-test`.

## Quick Start (Smallest Useful Run First)

Use this order unless the user requests otherwise:

0. After editing Python files, format before running tests: `nox -Re formatters`
1. Run sanity or targeted unit tests for changed files first.
2. Expand to broader unit coverage only if needed.
3. Run integration tests only when behavior changed and a Proxmox environment is configured.

## When to Invoke

TRIGGER when:

- A user asks to run tests, check tests, or verify changes with tests
- A user asks how to test a module or utility
- A user asks to write tests for new or modified code

DO NOT TRIGGER when:

- Reviewing a PR for overall quality
- The question is about module logic unrelated to testing

## Test Infrastructure

The collection must be installed at `ansible_collections/community/proxmox/` (relative to a directory on `ANSIBLE_COLLECTIONS_PATHS`) for imports to resolve correctly.

Use `nox` first because CI is built on antsibull-nox sessions. Direct `ansible-test` commands are useful for targeted local runs.

Most Proxmox integration targets are marked `unsupported` and require a real Proxmox environment configured in `tests/integration/integration_config.yml`. Docker/Podman wraps `ansible-test` execution, but it does not provide a Proxmox environment.

---

## Test Commands

### Preferred (CI-aligned): nox

```bash
# format (run after editing Python; CI lint gate)
nox -Re formatters

# verify lint without auto-fix (optional)
nox -Re codeqa

# sanity
nox -Re ansible-test-sanity-devel

# unit (all)
nox -Re ansible-test-units-devel

# unit (single Python version, faster)
nox -Re ansible-test-units-devel -- --python 3.13

# targeted unit file
nox -Re ansible-test-units-devel -- --python 3.13 tests/unit/plugins/modules/test_proxmox_user.py
```

### Sanity

Checks style, documentation, and imports for a changed file:

```bash
ansible-test sanity plugins/modules/proxmox_user.py --docker -vvv
```

### Unit

Runs unit tests for changed files:

```bash
ansible-test units tests/unit/plugins/modules/test_proxmox_user.py --docker -vvv
```

Unit tests live under `tests/unit/plugins/` and use the `pytest` framework.

### Integration

Runs integration tests against a configured Proxmox environment (started by Docker):

```bash
ansible-test integration proxmox_pool --docker -v --allow-unsupported
```

Integration tests live under `tests/integration/targets/<target_name>/`.

---

## Test Expectations

- Python code changes: run `nox -Re formatters` before tests.
- Documentation-only changes: run sanity tests.
- Code changes: run sanity and targeted unit tests at minimum.
- Behavior changes in modules: also run targeted integration tests when a Proxmox environment is available.
- New modules and bug fixes: add tests that cover the changed behavior.

## Failure Triage

When tests fail, classify first and then act:

- **Ruff/formatting failures**: run `nox -Re formatters`, then optionally `nox -Re codeqa` to verify, and retry tests.
- **Collection import/path failures**: verify working directory and collection path (`ansible_collections/community/proxmox/` on `ANSIBLE_COLLECTIONS_PATHS`).
- **Container runtime issues (`--docker`)**: verify Docker/Podman availability; rerun with the same command after fixing runtime access.
- **Unsupported integration target**: use `--allow-unsupported`; still requires real Proxmox environment and valid `tests/integration/integration_config.yml`.
- **Missing dependencies/environment**: report exact missing tool/config and provide the minimal command to retry.
- **Likely flaky/transient failure**: rerun once, then report both outcomes.

If failure root cause is unclear, return the first failing test and full error context instead of guessing.

---

## Integration Test Pattern

For state-changing modules, integration targets should usually follow this sequence:

1. Call the module under test → `register: result`
2. Assert on `result` using `ansible.builtin.assert`
3. Verify the resulting state independently → `register: result` → `ansible.builtin.assert`
4. Add `check_mode: true` coverage for operations that support check mode

```yaml
- name: Create pool in check mode
  check_mode: true
  community.proxmox.proxmox_pool:
    poolid: test-pool
  register: result

- name: Assert changed
  ansible.builtin.assert:
    that:
      - result is changed
      - result is success

- name: Create pool in real mode
  community.proxmox.proxmox_pool:
    poolid: test-pool
  register: result

- name: Assert changed
  ansible.builtin.assert:
    that:
      - result is changed
      - result is success
      - result.poolid == "{{ poolid }}"
```

Tests must also cover:

- **Idempotency**: run the same task a second time and assert `result is not changed`.
- **`state: absent`**: where applicable, remove the resource and assert it is gone.
- **Failure paths**: where applicable, assert expected failures and messages.

## Reporting Template

When returning test results, include:

- Commands executed
- Scope (targeted file/target vs full suite)
- Result summary (pass/fail)
- First failing test (if any) and likely cause
- Next recommended step

## Python Version Policy

- Use a single recent Python version (`--python 3.13`) for fast local validation unless broader coverage is requested.
- When validating CI parity or release readiness, run the full configured matrix/session.
