#!/usr/bin/env bash
set -euo pipefail

DEPLOY_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${DEPLOY_DIR}/app"
SOURCE_REPOSITORY="${CCR_SOURCE_REPOSITORY:-https://github.com/musistudio/claude-code-router.git}"
SOURCE_REF="${CCR_SOURCE_REF:-f22f2a4c79b2ad51b2b947377f285769470f6e09}"

cd "${DEPLOY_DIR}"

for required_command in git docker; do
  if ! command -v "${required_command}" >/dev/null 2>&1; then
    echo "Missing required command: ${required_command}" >&2
    exit 1
  fi
done

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is required (docker compose)." >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  if command -v openssl >/dev/null 2>&1; then
    WEB_AUTH_TOKEN="$(openssl rand -hex 32)"
  else
    WEB_AUTH_TOKEN="$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')"
  fi

  umask 077
  cp .env.example .env
  sed -i "s/replace-with-a-random-64-character-value/${WEB_AUTH_TOKEN}/" .env
  echo "Created private deployment configuration: ${DEPLOY_DIR}/.env"
fi

if [[ ! -d "${SOURCE_DIR}/.git" ]]; then
  git clone --filter=blob:none --no-checkout "${SOURCE_REPOSITORY}" "${SOURCE_DIR}"
fi

if [[ -n "$(git -C "${SOURCE_DIR}" status --porcelain)" ]]; then
  echo "The generated source directory contains local changes: ${SOURCE_DIR}" >&2
  echo "Move those changes away before running this script again." >&2
  exit 1
fi

git -C "${SOURCE_DIR}" fetch --depth 1 origin "${SOURCE_REF}"
git -C "${SOURCE_DIR}" checkout --detach FETCH_HEAD

docker compose up -d --build
docker compose ps

echo
echo "CCR is running. Keep the host port bound to 127.0.0.1 and use ccrAdmin over SSH."
echo "Read ${DEPLOY_DIR}/README.md for the desktop connection fields."
