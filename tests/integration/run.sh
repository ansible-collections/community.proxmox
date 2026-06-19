#!/usr/bin/env bash
# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INTEGRATION_CONFIG="${ROOT_DIR}/tests/integration/integration_config.yml"
INTEGRATION_CONFIG_TEMPLATE="${ROOT_DIR}/tests/integration/integration_config.yml.template"

IMAGE_NAME="dockurr/proxmox"
CONTAINER_NAME=""

PVE_API_TIMEOUT=30

VERSION=""
TARGET=""
IMAGE=""
REUSE=false
RM=false
PRUNE=false

trap 'echo "[INFO] Interrupted, cleaning up..."; cleanup; exit 130' INT TERM

help() {
  cat <<EOF
Usage: $0 [--version VERSION] [--target TARGET] [--reuse] [--rm] [--prune]

Run integration tests against a Proxmox VE container.

Options:
  --version VERSION   Proxmox version (major like 9, exact like 9.2.3, latest, or digest like sha256:...)
  --target TARGET     ansible-test integration target (e.g. proxmox_pool)
  --reuse             Reuse existing container if present
  --rm                Remove container after tests
  --prune             Remove the container image (implies --rm)

Defaults:
  --version           latest
  --target            all integration test targets
  --reuse             off (recreate container if one already exists)
  --rm                off (keep container after tests)
  --prune             off (keep container image)

Examples:
  $0
  $0 --version sha256:abc123
  $0 --version sha256:abc123 --target proxmox_pool
  $0 --target proxmox_pool
  $0 --version 9 --target proxmox_pool
  $0 --reuse --target proxmox_pool
  $0 --rm --prune
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
  --version)
    VERSION="${2:?'--version requires a value'}"
    shift 2
    ;;
  --target)
    TARGET="${2:?'--target requires a value'}"
    shift 2
    ;;
  --reuse)
    REUSE=true
    shift
    ;;
  --rm)
    RM=true
    shift
    ;;
  --prune)
    PRUNE=true
    RM=true
    shift
    ;;
  --help | -h)
    help
    exit 0
    ;;
  *)
    echo "Unknown option: $1" >&2
    help
    exit 1
    ;;
  esac
done

VERSION="${VERSION:-latest}"

check_prerequisites() {
  echo "[INFO] Checking prerequisites"

  local missing=false

  if ! command -v docker &>/dev/null; then
    echo "[ERROR] docker not found." >&2
    missing=true
  fi
  if ! command -v yq &>/dev/null; then
    echo "[ERROR] yq not found." >&2
    missing=true
  fi
  if ! command -v curl &>/dev/null; then
    echo "[ERROR] curl not found." >&2
    missing=true
  fi
  if ! command -v ansible-test &>/dev/null; then
    echo "[ERROR] ansible-test not found." >&2
    missing=true
  fi
  if [[ ! -e /dev/kvm ]]; then
    echo "[ERROR] KVM acceleration is not available (/dev/kvm is missing)." >&2
    missing=true
  fi

  if $missing; then
    echo "[ERROR] Missing prerequisites. Please setup the missing prerequisites and try again." >&2
    exit 1
  fi
}

ensure_integration_config() {
  if [[ -f "${INTEGRATION_CONFIG}" ]]; then
    return
  fi

  if [[ ! -f "${INTEGRATION_CONFIG_TEMPLATE}" ]]; then
    echo "[ERROR] Missing template: ${INTEGRATION_CONFIG_TEMPLATE}" >&2
    exit 1
  fi

  echo "[INFO] Creating integration_config.yml from template"
  cp "${INTEGRATION_CONFIG_TEMPLATE}" "${INTEGRATION_CONFIG}"
}

resolve_image() {
  local version="$1"
  if [[ "${version}" =~ ^sha256: ]]; then
    echo "${IMAGE_NAME}@${version}"
  else
    echo "${IMAGE_NAME}:${version}"
  fi
}

resolve_hostname() {
  yq -r '.api_host' "${INTEGRATION_CONFIG}"
}

pull_image() {
  local image="$1"

  if ! docker pull "${image}"; then
    echo "[ERROR] Failed to pull image: ${image}" >&2
    echo "[ERROR] Verify the version/tag exists for ${IMAGE_NAME}" >&2
    exit 1
  fi
}

container_exists() {
  [[ -n "${CONTAINER_NAME}" ]] || return 1
  docker container ls -a --format '{{.Names}}' | grep -q "${CONTAINER_NAME}" >/dev/null
}

wait_for_api() {
  local host url elapsed=0

  host=$(resolve_hostname)
  url="https://${host}:8006/"

  while true; do
    if curl -skf --max-time 5 -o /dev/null "${url}" 2>&1; then
      break
    fi

    if ((elapsed >= PVE_API_TIMEOUT)); then
      echo "[ERROR] PVE API is not ready" >&2
      exit 1
    fi

    sleep 5
    elapsed=$((elapsed + 5))
    echo "  still waiting... (${elapsed}s elapsed)"
  done
}

cleanup() {
  set +e
  if container_exists; then
    echo "[INFO] Stopping container"
    docker stop "${CONTAINER_NAME}" >/dev/null 2>&1
    if $RM; then
      echo "[INFO] Deleting container"
      docker rm "${CONTAINER_NAME}" >/dev/null 2>&1
    fi
  fi
  if $PRUNE && [[ -n ${IMAGE} ]]; then
    echo "[INFO] Deleting image"
    docker image rm "${IMAGE}" >/dev/null 2>&1
  fi
}

start() {
  IMAGE=$(resolve_image "${VERSION}")
  CONTAINER_NAME="pve-integration-${VERSION}"

  echo "[INFO] Starting container using: ${IMAGE}"
  pull_image "${IMAGE}"

  if ! $REUSE && container_exists; then
    docker stop "${CONTAINER_NAME}" >/dev/null
    docker rm "${CONTAINER_NAME}" >/dev/null
  fi

  if $REUSE && container_exists; then
    docker start "${CONTAINER_NAME}"
  else
    docker run -d --name "${CONTAINER_NAME}" --hostname pve --privileged \
      -e "PASSWORD=root" -p 8006:8006 --stop-timeout 120 "${IMAGE}" >/dev/null
  fi

  echo "[INFO] Waiting for PVE API to be ready"
  wait_for_api

  echo "[INFO] Running tests"
  local rc=0
  ansible-test integration ${TARGET:+"${TARGET}"} -v --allow-unsupported || rc=$?
  cleanup
  return "$rc"
}

main() {
  check_prerequisites
  ensure_integration_config
  start
}

main "$@"
