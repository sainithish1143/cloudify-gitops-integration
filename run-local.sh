#!/usr/bin/env bash
set -euo pipefail

DEPLOYMENT_FILE="${1:-deployments/hello-dev.yaml}"
OPERATION="${2:-install}"

if [ ! -f .env ]; then
  echo ".env not found. Create it from .env.example first."
  echo "cp .env.example .env"
  exit 1
fi

docker compose run --rm cloudify-gitops-runner \
  scripts/manual_lifecycle_from_deployment.py \
  --deployment-file "${DEPLOYMENT_FILE}" \
  --operation "${OPERATION}"
