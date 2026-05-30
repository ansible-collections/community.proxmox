<!--
Copyright (c) Ansible Project
GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
SPDX-License-Identifier: GPL-3.0-or-later
-->

# AGENTS.md

This file is intended for AI coding agents. It is kept human-readable so contributors can also use it as a quick-reference guide.

When official documentation is not explicitly provided or it's insufficient, you MUST delegate to the `docs-explorer` subagent (see `.agents/subagents/docs-explorer.md`) to look up current official documentation for the relevant libraries and technologies.

## What This Project Is

An Ansible collection (`community.proxmox`) providing modules for managing [Proxmox VE](https://www.proxmox.com) — a virtualization management platform. No roles exist — only modules and shared utilities.

## Development Environment

The collection must reside at `ansible_collections/community/proxmox/` (relative to a directory on `ANSIBLE_COLLECTIONS_PATHS`) for imports to resolve correctly.

For test commands, patterns, and requirements see `.agents/skills/run-tests/SKILL.md`.

## Agent Operating Procedure

Classify the request before acting:

1. `code_change`: implement requested behavior in the smallest safe scope
2. `testing`: run or add tests using `.agents/skills/run-tests/SKILL.md`
3. `docs_lookup`: verify external API/framework behavior with the docs-explorer subagent
4. `review_or_question`: analyze existing code and return findings/answers without unrelated edits

Execution policy:

- Run safe local checks and targeted tests proactively for changed code.
- Ask before long-running, destructive, or environment-dependent operations when intent is unclear.
- Never mix unrelated refactors with the requested task.

## Preferred Documentation Sources

Use official and canonical documentation first. Prefer sources in this order:

1. Official project documentation and API references
2. Official collection/community contributor documentation
3. Secondary sources (blog posts, forums, Q&A) only for extra context

Preferred sources:

- Ansible developer guide: <https://docs.ansible.com/ansible/latest/dev_guide/>
- Ansible collection contributor docs: <https://docs.ansible.com/projects/ansible/latest/community/contributions_collections.html>
- Ansible developing modules docs: <https://docs.ansible.com/projects/ansible/latest/dev_guide/developing_modules_general.html>
- Ansible module documentation format and conventions (use for module docstrings and `DOCUMENTATION`/`EXAMPLES`/`RETURN`): <https://docs.ansible.com/projects/ansible/latest/dev_guide/developing_modules_documenting.html#developing-modules-documenting>
- Ansible module `argument_spec` and option constraints (use for `module_args()`, `module_options()`, and `create_proxmox_module()`): <https://docs.ansible.com/projects/ansible/latest/dev_guide/developing_program_flow_modules.html#argument-spec>
- Proxmox VE API viewer: <https://pve.proxmox.com/pve-docs/api-viewer/index.html>
- Proxmox VE documentation: <https://pve.proxmox.com/pve-docs/>
- Proxmox wiki: <https://pve.proxmox.com/wiki/Main_Page>

## Coding Guidelines

- Follow these software development principles: KISS (Keep It Simple, Stupid), DRY (Don't Repeat Yourself), YAGNI (You Aren't Gonna Need It), Separation of Concerns, Composition over Inheritance, and Convention Over Configuration.
- Prioritize code simplicity and readability over flexibility.
- Favor simple, short, and easily testable functions with no side effects over classes. Use classes only when they naturally fit the problem and help avoid boilerplate code while grouping tightly related functionality.
- Use `snake_case` for all variable and parameter names.
- Shared code used by multiple modules belongs in `plugins/module_utils/` (DRY principle). Do not duplicate connection or utility logic in individual modules.
- Do not add connection parameters to individual modules. Extend the `proxmox` doc fragment in `plugins/doc_fragments/proxmox.py` instead.
- All code changes must pass sanity and unit tests. Run integration tests for behavior changes in a configured Proxmox environment.
- Keep each piece of work focused on solving a single, specific issue or task. Do not mix unrelated changes (e.g., a bugfix and an unrelated refactoring) in the same branch or PR.
- Use conventional commit message prefixes: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `ci:`. Add a scope with the module name when applicable (e.g. `proxmox_pool`, `proxmox_storage`). Example: `fix(proxmox_pool): handle nested pool`.

## Development Conventions

- Every PR that changes module behavior needs a changelog fragment in `changelogs/fragments/<something>.yaml`. Docs/tests/refactoring PRs are exempt and also new modules. Valid fragment sections: `major_changes`, `minor_changes`, `bugfixes`, `breaking_changes`, `deprecated_features`, `removed_features`, `security_fixes`, `known_issues`, `trivial`. Fragments are consumed (deleted) at release time (`keep_fragments: false` in `changelogs/config.yaml`).

## Definition of Done

Before finalizing work, verify:

- Requested behavior is implemented in the intended scope only.
- Relevant sanity/unit tests are run (and integration tests for behavior changes when environment is available), or a clear reason is provided if not run.
- Changed files are free of newly introduced lint/sanity issues.
- Changelog fragment requirement is evaluated for behavior changes.
- Response includes key outcomes, risks, and any follow-up actions needed.

## Subagents

Subagent definitions live in `.agents/subagents/`. When a task matches a subagent's trigger conditions, delegate to it.

## Agent Skills

Skills live in `.agents/skills/*/SKILL.md`. At session start, scan and register all skills. When a request matches a skill's trigger, load and apply it.
