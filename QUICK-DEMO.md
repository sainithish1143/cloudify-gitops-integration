# Quick Demo Commands

## Default deployment

Create/reconcile environment:

```bash
echo "# env $(date)" >> deployments/wr-demo-gitops-hello.yaml
git add deployments/*.yaml
git commit -m "Create Cloudify environment"
git push
```

Execute install:

```bash
echo "# install $(date)" >> operations/wr-demo-gitops-hello-install.yaml
git add operations/*.yaml
git commit -m "Run install workflow"
git push
```

Execute configure with updated input:

```bash
vi inputs/hello/gitops-hello.yaml
echo "# configure $(date)" >> operations/wr-demo-gitops-hello-configure.yaml
git add inputs/hello/*.yaml operations/*.yaml
git commit -m "Run configure workflow with updated inputs"
git push
```

Delete environment:

```bash
git rm deployments/wr-demo-gitops-hello.yaml
git commit -m "Remove Cloudify environment"
git push
```

## Optional uninstall workflow

If the blueprint exposes an `uninstall` workflow, enable the sample:

```bash
cp operations/wr-demo-gitops-hello-uninstall.yaml.sample operations/wr-demo-gitops-hello-uninstall.yaml
git add operations/wr-demo-gitops-hello-uninstall.yaml
git commit -m "Run uninstall workflow"
git push
```
