#!/usr/bin/env python3
"""Manual helper to execute install/update/uninstall from one deployment desired-state file."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from gitops_reconcile import expand_env_vars, load_yaml_file, normalize_deployment_spec


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deployment-file", required=True)
    parser.add_argument("--operation", required=True, choices=["install", "update", "uninstall"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo = Path.cwd()
    spec = load_yaml_file(repo / args.deployment_file)
    request = normalize_deployment_spec(spec, args.operation, repo)
    if args.dry_run:
        request["dry_run"] = True
    temp_dir = Path(tempfile.mkdtemp(prefix="cfy-manual-request-"))
    request_path = temp_dir / f"manual-{request['deployment_id']}-{args.operation}.yaml"
    request_path.write_text(yaml.safe_dump(expand_env_vars(request), sort_keys=False), encoding="utf-8")
    print(f"Generated request: {request_path}")
    print(f"operation={args.operation} deployment_id={request['deployment_id']} blueprint_id={request['blueprint_id']}")
    return subprocess.run([sys.executable, "scripts/cloudify_lifecycle.py", "--request", str(request_path)], cwd=str(repo)).returncode


if __name__ == "__main__":
    sys.exit(main())
