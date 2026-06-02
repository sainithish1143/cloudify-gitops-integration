# Cloudify GitOps: Environment + Workflow Intent Model

This repo demonstrates a production-style Cloudify integration that can be triggered by GitHub Actions today and by Jenkins later using the same scripts.

## Core idea

```text
deployments/*.yaml commit  -> create/register Cloudify environment only
operations/*.yaml commit   -> execute the requested Cloudify workflow
deployments/*.yaml delete  -> uninstall/delete based on deletion policy
```

This avoids hardcoding `install` or `update` into GitOps. The user explicitly provides the Cloudify workflow name in an operation intent file.

## Repo layout

```text
.github/workflows/cloudify-envops.yml
scripts/
  cloudify_lifecycle.py
  gitops_reconcile.py
  manual_lifecycle_from_deployment.py
deployments/
  hello-dev.yaml
operations/
  hello-dev-install.yaml
  hello-dev-configure.yaml
  hello-dev-uninstall.yaml
blueprints/hello/
inputs/hello/dev.yaml
workflow-params/execute-configure.yaml
```

## GitHub setup

Use a self-hosted runner when Cloudify is on local Minikube, for example `http://192.168.49.2`.

Repository secrets:

```text
CFY_MANAGER_URL = http://192.168.49.2
CFY_USERNAME    = admin
CFY_PASSWORD    = admin
CFY_TENANT      = default_tenant
```

Repository variables:

```text
CFY_API_VERSION = v3.1
CFY_INSECURE = true
GITOPS_MULTI_DEPLOYMENT_MODE = all
```

## Demo flow

### 1. Create Cloudify environment

Commit the deployment desired-state file:

```bash
git add deployments/hello-dev.yaml
git commit -m "Create hello dev Cloudify environment"
git push
```

Action: uploads/registers blueprint and creates Cloudify deployment. It does not run `install`.

### 2. Execute install workflow

Commit operation intent:

```bash
git add operations/hello-dev-install.yaml
git commit -m "Run install workflow for hello dev"
git push
```

Action: executes the workflow from the operation file:

```yaml
workflow: install
```

### 3. Show user inputs in logs

Update user/demo inputs:

```bash
vi inputs/hello/dev.yaml
```

Then commit an operation intent. For configure demo:

```bash
git add inputs/hello/dev.yaml operations/hello-dev-configure.yaml
git commit -m "Run configure workflow with updated Git input values"
git push
```

The operation uses `execute_operation` and injects the latest input values as `operation_kwargs`, so Cloudify execution logs show the committed input values.

### 4. Execute any custom workflow

Create a new operation file:

```yaml
apiVersion: cloudify.windriver.com/v1
kind: CloudifyOperation

metadata:
  name: hello-dev-custom-workflow

spec:
  deployment_ref: deployments/hello-dev.yaml
  workflow: my_custom_workflow
  wait: true
  timeout_sec: 3600
  parameters:
    key1: value1
    key2: value2
```

Commit it:

```bash
git add operations/hello-dev-custom-workflow.yaml
git commit -m "Run custom Cloudify workflow"
git push
```

### 5. Delete deployment/environment

For demo, `deployments/hello-dev.yaml` has:

```yaml
deletion_policy: auto_uninstall_delete
```

So deleting the deployment file runs uninstall and deletes the Cloudify deployment:

```bash
git rm deployments/hello-dev.yaml
git commit -m "Remove hello dev Cloudify environment"
git push
```

For production, set:

```yaml
deletion_policy: manual
```

Then users must commit an explicit uninstall operation before removing the deployment file.

## Jenkins later

Jenkins should use the same scripts:

```bash
python3 scripts/gitops_reconcile.py --before <old_sha> --after <new_sha>
```

Manual Jenkins jobs should use:

```bash
python3 scripts/manual_lifecycle_from_deployment.py \
  --deployment deployments/hello-dev.yaml \
  --action execute-workflow \
  --workflow install
```

So Jenkins and GitOps share the same deployment model and lifecycle engine.
