# GitOps Package V3 - Visible Verification

This package is the GitOps-only package with the final naming and multi-deployment changes.

Visible changes in this package:

1. Main deployment file uses source-specific name without dev suffix:
   - deployments/wr-demo-gitops-hello.yaml
   - deployment id: wr-demo-gitops-hello
   - blueprint id: wr-demo-gitops-hello-bp

2. Operation files use the same source-specific naming:
   - operations/wr-demo-gitops-hello-install.yaml
   - operations/wr-demo-gitops-hello-configure.yaml
   - operations/wr-demo-gitops-hello-uninstall.yaml.sample

3. Multiple deployment examples are included:
   - examples/multi-deployment/deployments/wr-demo-gitops-app1.yaml
   - examples/multi-deployment/deployments/wr-demo-gitops-app2.yaml
   - examples/multi-deployment/operations/wr-demo-gitops-app1-install.yaml
   - examples/multi-deployment/operations/wr-demo-gitops-app2-install.yaml

4. Uninstall sample is included as .yaml.sample so it will not execute accidentally.
   Rename to .yaml only if the blueprint exposes an uninstall workflow.

5. GitOps and Jenkins packages are intentionally separate repos, but the common scripts are aligned.
