# Cloudify GitOps Lifecycle Procedure

This repo uses request YAML files as the source of truth for Cloudify lifecycle actions.

## Supported trigger modes

### 1. Manual GitHub Actions run

Go to:

```text
Actions -> Cloudify Lifecycle GitOps -> Run workflow
```

Use one of:

```text
requests/hello-dev-install.yaml
requests/hello-dev-update.yaml
requests/hello-dev-uninstall.yaml
```

Optional manual overrides:

```text
deployment_id = app1-dev
blueprint_id  = app1-bp
dry_run       = true|false
```

### 2. Commit-based GitOps run

For commit-based GitOps, the request YAML is the source of truth. The workflow runs the changed request file(s).

Install:

```bash
vi requests/hello-dev-install.yaml
git add requests/hello-dev-install.yaml
git commit -m "Install hello dev through Cloudify GitOps"
git push
```

Update:

```bash
vi requests/hello-dev-update.yaml
git add requests/hello-dev-update.yaml
git commit -m "Update hello dev through Cloudify GitOps"
git push
```

Uninstall:

```bash
vi requests/hello-dev-uninstall.yaml
git add requests/hello-dev-uninstall.yaml
git commit -m "Uninstall hello dev through Cloudify GitOps"
git push
```

## Per-deployment request files

For production, create one set of request files per application/environment/deployment:

```text
requests/app1-dev-install.yaml
requests/app1-dev-update.yaml
requests/app1-dev-uninstall.yaml
requests/app2-prod-install.yaml
requests/app2-prod-update.yaml
requests/app2-prod-uninstall.yaml
```

Each file should explicitly set:

```yaml
blueprint_id: app1-bp
deployment_id: app1-dev
operation: install
workflow: install
```

For update/uninstall, use the same `deployment_id` used for install.

## Multiple request files in one commit

Controlled by repository variable:

```text
GITOPS_MULTI_REQUEST_MODE
```

Supported values:

```text
all   -> execute all changed request files in sorted order
first -> execute only the first changed request file
fail  -> fail if more than one request file changed
```

Default is `all`.

## Safe no-op behavior

If a commit changes blueprint/input/script files but no request YAML changes, the workflow does not execute Cloudify by default.

To intentionally run a default request for non-request commits, create repository variable:

```text
DEFAULT_REQUEST_FILE=requests/hello-dev-update.yaml
```

## Required GitHub Secrets

```text
CFY_MANAGER_URL
CFY_USERNAME
CFY_PASSWORD
CFY_TENANT
```

For local Minikube Cloudify, use a self-hosted runner and set:

```text
CFY_MANAGER_URL=http://192.168.49.2
```

## Optional GitHub Variables

```text
CFY_API_VERSION=v3.1
CFY_INSECURE=true
LOG_LEVEL=INFO
GITOPS_MULTI_REQUEST_MODE=all
DEFAULT_REQUEST_FILE=
```

## Request safety controls

Disable a request without deleting it:

```yaml
enabled: false
```

or:

```yaml
disabled: true
```

Validate only, no Cloudify API calls:

```yaml
dry_run: true
```

## Logs and audit

Every run writes:

```text
logs/cloudify-lifecycle-<run_id>.log
logs/cloudify-lifecycle-<run_id>.summary.json
```

The workflow uploads `logs/` as a GitHub Actions artifact.
