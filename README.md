# Cloudify GitOps Lifecycle Integration

Production-grade GitOps integration for invoking Cloudify blueprint lifecycle actions from GitHub Actions using a reusable Python runner.

## Flow

```text
Git commit or manual workflow
  -> GitHub Actions workflow
  -> scripts/cloudify_lifecycle.py
  -> Cloudify Manager
  -> blueprint upload / deployment create / workflow execute / uninstall / delete
```

## Key properties

- Same request YAML contract for install, update, execute, uninstall and delete
- Commit-based request selection
- Manual workflow override support
- Self-hosted runner friendly for local/private Cloudify Manager
- Idempotency controls for existing blueprints/deployments
- Retry/backoff for transient API/network failures
- Execution polling with timeout
- Secret masking in logs/audit
- Per-run log file and JSON audit summary
- Safe no-op behavior when no request YAML changes
- Supports multiple request files in one commit with configurable policy

## Required setup

GitHub repository secrets:

```text
CFY_MANAGER_URL
CFY_USERNAME
CFY_PASSWORD
CFY_TENANT
```

Optional repository variables:

```text
CFY_API_VERSION=v3.1
CFY_INSECURE=true
LOG_LEVEL=INFO
GITOPS_MULTI_REQUEST_MODE=all
DEFAULT_REQUEST_FILE=
```

For Minikube/local Cloudify IP such as `http://192.168.49.2`, use a GitHub self-hosted runner on the same machine/network.

## Run manually

```text
Actions -> Cloudify Lifecycle GitOps -> Run workflow
```

Request files:

```text
requests/hello-dev-install.yaml
requests/hello-dev-update.yaml
requests/hello-dev-uninstall.yaml
```

## Run by commit

```bash
git add requests/hello-dev-install.yaml
git commit -m "Install hello dev through Cloudify GitOps"
git push
```

The workflow selects the changed request YAML and executes it.

## Local validation

```bash
cp .env.example .env
vi .env
./run-compose.sh requests/hello-dev-install.yaml
```

## Docs

See:

```text
docs/GITOPS_PROCEDURE.md
docs/PRODUCTION_GRADE_DESIGN.md
docs/DOCKER_COMPOSE_RUN.md
docs/ARCHITECTURE.md
```
