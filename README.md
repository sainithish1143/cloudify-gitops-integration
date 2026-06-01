# Cloudify GitOps Lifecycle Automation

This repository demonstrates and provides a production-ready GitOps mechanism to invoke Cloudify blueprint lifecycle operations.

A Git commit or manual GitHub Actions run executes the same reusable lifecycle runner:

```text
Git commit -> GitHub Actions -> scripts/cloudify_lifecycle.py -> Cloudify Manager
```

## Layout

```text
.github/workflows/cloudify-lifecycle.yml   # GitOps workflow
scripts/cloudify_lifecycle.py              # Common production-grade Cloudify runner
requests/                                  # Lifecycle intent YAML files
blueprints/hello/                          # Example Cloudify blueprint
inputs/dev.yaml                            # Example deployment inputs
Dockerfile / docker-compose.yml            # Optional local runner
logs/                                      # Runtime logs, ignored by Git
```

## Production controls included

The runner includes request validation, Cloudify credential validation, blueprint/input path validation, retry with backoff, execution polling, timeout handling, idempotency controls, dry-run support, secret masking, per-run log file, JSON summary, and non-zero exit codes for automation failures.

## Configure GitHub Actions secrets

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

Optional GitHub variables:

```text
CFY_API_VERSION=v3.1
CFY_INSECURE=true
```

## Trigger GitOps manually

Go to:

```text
GitHub repo -> Actions -> Cloudify Lifecycle GitOps -> Run workflow
```

Use:

```text
requests/hello-dev-install.yaml
```

## Trigger GitOps by commit

Change or add a request file:

```bash
cp requests/hello-dev-install.yaml requests/my-app-dev-install.yaml
vi requests/my-app-dev-install.yaml
git add requests/my-app-dev-install.yaml
git commit -m "Trigger Cloudify install from GitOps"
git push
```

GitHub Actions will run:

```bash
python3 scripts/cloudify_lifecycle.py --request requests/my-app-dev-install.yaml
```

## Local test before pushing

```bash
cp .env.example .env
vi .env
./run-compose.sh requests/hello-dev-install.yaml
```
