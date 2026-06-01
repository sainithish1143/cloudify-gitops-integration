# GitOps Procedure

## Goal

Cloudify lifecycle should be triggered from Git commits using the same script used by Jenkins:

```bash
python3 scripts/cloudify_lifecycle.py --request <request-file>
```

## Folder used by GitOps

GitHub Actions watches only:

```text
requests/gitops/**
```

It does not run request files from:

```text
requests/jenkins/**
```

This avoids duplicate lifecycle execution when the same repo is used for both demos and production flows.

## Configure GitHub secrets

Go to:

```text
GitHub repo -> Settings -> Secrets and variables -> Actions -> New repository secret
```

Add:

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
```

## Manual GitOps run

Go to:

```text
GitHub repo -> Actions -> Cloudify Lifecycle GitOps -> Run workflow
```

Use:

```text
requests/gitops/hello-dev-install.yaml
```

## Commit-driven GitOps run

Modify a GitOps request file:

```bash
vi requests/gitops/hello-dev-install.yaml
git add requests/gitops/hello-dev-install.yaml
git commit -m "Trigger Cloudify GitOps install"
git push
```

GitHub Actions will:

1. checkout the repo
2. install Python dependencies
3. validate Cloudify secrets
4. select changed files from `requests/gitops/**`
5. run `scripts/cloudify_lifecycle.py`
6. upload logs as workflow artifacts

## Add a new app

```bash
cp requests/gitops/hello-dev-install.yaml requests/gitops/my-app-dev-install.yaml
vi requests/gitops/my-app-dev-install.yaml
```

Change at least:

```yaml
blueprint_id: my-app-bp
deployment_id: my-app-dev
blueprint_dir: blueprints/my-app
inputs_files:
  - inputs/my-app-dev.yaml
```

Commit and push:

```bash
git add requests/gitops/my-app-dev-install.yaml blueprints/my-app inputs/my-app-dev.yaml
git commit -m "Add GitOps lifecycle for my app"
git push
```
