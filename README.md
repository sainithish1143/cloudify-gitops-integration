# Cloudify Desired-State GitOps E2E

This repository demonstrates a production-oriented GitOps mechanism for invoking Cloudify blueprint lifecycle operations.

The model is based on desired-state deployment files:

```text
deployments/<deployment-name>.yaml
```

Lifecycle is derived from Git changes:

```text
Added deployment file    -> install
Modified deployment file -> update
Deleted deployment file  -> uninstall
```

Each deployment file owns its unique lifecycle configuration: blueprint, inputs, tenant, workflow, retry, timeout, and uninstall policy.

## Structure

```text
.github/workflows/cloudify-desired-state.yml
scripts/cloudify_lifecycle.py
scripts/gitops_reconcile.py
scripts/manual_lifecycle_from_deployment.py
deployments/hello-dev.yaml
blueprints/hello/blueprint.yaml
blueprints/hello/scripts/lifecycle.py
inputs/hello/dev.yaml
```

## Demo input behavior

`inputs/hello/dev.yaml` contains user/demo inputs:

```yaml
customer_name: "Demo Customer"
application_name: "hello-gitops-service"
environment: "dev"
message: "This value came from GitOps input file and is visible in Cloudify execution logs"
replicas: 2
```

During Cloudify blueprint execution, these values are printed in the Cloudify execution logs by `blueprints/hello/scripts/lifecycle.py`.

## GitHub setup

Because `http://192.168.49.2` is a local Minikube IP, use a self-hosted GitHub Actions runner on the machine/network that can reach Cloudify.

Add repository secrets:

```text
CFY_MANAGER_URL=http://192.168.49.2
CFY_USERNAME=admin
CFY_PASSWORD=admin
CFY_TENANT=default_tenant
```

Add repository variables:

```text
CFY_API_VERSION=v3.1
CFY_INSECURE=true
GITOPS_MULTI_DEPLOYMENT_MODE=all
```

## Commit-based GitOps

### Install

Create a new deployment desired-state file:

```bash
cp deployments/hello-dev.yaml deployments/app1-dev.yaml
vi deployments/app1-dev.yaml
```

Update `metadata.name`, `spec.blueprint.id`, `spec.deployment.id`, and input files if needed.

Commit:

```bash
git add deployments/app1-dev.yaml
git commit -m "Add app1-dev Cloudify deployment"
git push
```

The workflow detects the added file and runs install.

### Update

Modify the same deployment file or its referenced input file. For update based on deployment file modification:

```bash
vi deployments/app1-dev.yaml
git add deployments/app1-dev.yaml
git commit -m "Update app1-dev Cloudify deployment"
git push
```

The workflow detects the modified file and runs update.

### Uninstall

Delete the desired-state file:

```bash
git rm deployments/app1-dev.yaml
git commit -m "Remove app1-dev Cloudify deployment"
git push
```

The workflow reads the deleted file from the previous commit and runs uninstall for the correct deployment ID.

## Manual run from GitHub Actions

Go to:

```text
Actions -> Cloudify Desired-State GitOps -> Run workflow
```

Inputs:

```text
deployment_file = deployments/hello-dev.yaml
operation       = install | update | uninstall
dry_run         = false | true
```

## Local Docker Compose run

```bash
cp .env.example .env
vi .env
./run-local.sh deployments/hello-dev.yaml install
./run-local.sh deployments/hello-dev.yaml update
./run-local.sh deployments/hello-dev.yaml uninstall
```

## Production notes

- One deployment file represents one Cloudify deployment.
- Each deployment can use a different blueprint and different inputs.
- Delete operation uses previous Git content to know what to uninstall.
- All Cloudify calls use retry/backoff, timeouts, logging, and JSON summaries.
- Logs are uploaded as GitHub workflow artifacts.

## Referenced input/blueprint change behavior

The reconciler also handles production dependency changes:

```text
Change a deployment file             -> update that deployment
Change an input file referenced by a deployment -> update that deployment
Change a blueprint file under referenced blueprint source -> update that deployment
Delete a deployment file             -> uninstall using previous Git content
```

This means user-provided input changes can be committed under `inputs/` and the impacted deployment will be updated automatically.

Example:

```bash
vi inputs/hello/dev.yaml
git add inputs/hello/dev.yaml
git commit -m "Update hello-dev demo input values"
git push
```

The workflow finds deployments that reference `inputs/hello/dev.yaml` and runs update for those deployments.
