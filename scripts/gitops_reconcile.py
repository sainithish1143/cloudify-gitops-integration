#!/usr/bin/env python3
"""GitOps desired-state reconciler for Cloudify deployments.

It derives lifecycle operation from Git diff status on files under deployments/:
  A/R/C -> install
  M     -> update
  D     -> uninstall, using the previous file content from the before commit

It generates normalized lifecycle request YAML files and invokes cloudify_lifecycle.py.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml


def _strip(value: Optional[str]) -> str:
    return (value or "").strip()


def setup_logging(log_dir: Path, run_id: str, level: str = "INFO") -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("gitops-reconcile")
    logger.handlers.clear()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    file_handler = logging.FileHandler(log_dir / f"gitops-reconcile-{run_id}.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(stream)
    logger.addHandler(file_handler)
    return logger


def run_cmd(cmd: List[str], cwd: Path, check: bool = True) -> str:
    result = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nstdout={result.stdout}\nstderr={result.stderr}")
    return result.stdout


def load_yaml_text(text: str, source: str) -> Dict[str, Any]:
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Deployment spec must be a YAML object: {source}")
    return data


def load_yaml_file(path: Path) -> Dict[str, Any]:
    return load_yaml_text(path.read_text(encoding="utf-8"), str(path))


def get_changed_deployment_files(repo: Path, before: str, after: str) -> List[Tuple[str, str]]:
    output = run_cmd(["git", "diff", "--name-status", before, after, "--", "deployments"], repo, check=True)
    changes: List[Tuple[str, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") or status.startswith("C"):
            path = parts[-1]
            status_key = status[0]
        else:
            path = parts[-1]
            status_key = status[0]
        if path.startswith("deployments/") and path.endswith((".yaml", ".yml")):
            changes.append((status_key, path))
    return changes



def get_changed_files(repo: Path, before: str, after: str) -> List[Tuple[str, str]]:
    output = run_cmd(["git", "diff", "--name-status", before, after], repo, check=True)
    changes: List[Tuple[str, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") or status.startswith("C"):
            path = parts[-1]
            status_key = status[0]
        else:
            path = parts[-1]
            status_key = status[0]
        changes.append((status_key, path))
    return changes


def deployment_references_path(spec: Dict[str, Any], changed_path: str) -> bool:
    body = spec.get("spec") or {}
    blueprint = body.get("blueprint") or {}
    deployment = body.get("deployment") or {}
    blueprint_source = str(blueprint.get("source", "")).rstrip("/")
    if blueprint_source and (changed_path == blueprint_source or changed_path.startswith(blueprint_source + "/")):
        return True
    for input_file in deployment.get("inputs", []) or []:
        if changed_path == str(input_file):
            return True
    return False


def discover_dependency_update_deployments(repo: Path, changed_files: List[Tuple[str, str]], already_handled_paths: set[str], logger: logging.Logger) -> List[Tuple[str, str]]:
    dependency_paths = []
    for status, path in changed_files:
        if path.startswith("deployments/"):
            continue
        if path.startswith(("inputs/", "blueprints/")) and status in {"A", "M", "D", "R", "C"}:
            dependency_paths.append(path)
    if not dependency_paths:
        return []

    updates: List[Tuple[str, str]] = []
    seen: set[str] = set()
    for deployment_file in sorted(repo.glob("deployments/**/*.y*ml")):
        rel = str(deployment_file.relative_to(repo))
        if rel in already_handled_paths:
            continue
        try:
            spec = load_yaml_file(deployment_file)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping invalid deployment spec %s while checking dependency changes: %s", rel, exc)
            continue
        for changed_path in dependency_paths:
            if deployment_references_path(spec, changed_path):
                if rel not in seen:
                    updates.append(("M", rel))
                    seen.add(rel)
                    logger.info("Dependency change %s affects %s; scheduling update", changed_path, rel)
                break
    return updates

def previous_file_content(repo: Path, before: str, path: str) -> str:
    return run_cmd(["git", "show", f"{before}:{path}"], repo, check=True)


def normalize_deployment_spec(spec: Dict[str, Any], operation: str, repo: Path) -> Dict[str, Any]:
    if spec.get("kind") != "CloudifyDeployment":
        raise ValueError("kind must be CloudifyDeployment")
    metadata = spec.get("metadata") or {}
    body = spec.get("spec") or {}
    if not isinstance(metadata, dict) or not isinstance(body, dict):
        raise ValueError("metadata and spec must be objects")
    enabled = body.get("enabled", True)
    if enabled is False and operation != "uninstall":
        raise RuntimeError(f"Deployment spec {metadata.get('name')} is disabled; skipping non-uninstall operation")

    blueprint = body.get("blueprint") or {}
    deployment = body.get("deployment") or {}
    lifecycle = body.get("lifecycle") or {}
    execution = body.get("execution") or {}
    logging_cfg = body.get("logging") or {}
    manager = body.get("manager") or {}

    lifecycle_cfg = lifecycle.get(operation) or {}
    if operation == "update" and not lifecycle_cfg:
        lifecycle_cfg = lifecycle.get("install") or {}
    if operation == "uninstall" and not lifecycle_cfg:
        lifecycle_cfg = {"workflow": "uninstall", "wait": True, "timeout_sec": 3600, "delete_deployment": True, "delete_blueprint": False}

    deployment_id = _strip(deployment.get("id") or metadata.get("name"))
    blueprint_id = _strip(blueprint.get("id") or f"{deployment_id}-bp")
    if not deployment_id:
        raise ValueError("spec.deployment.id or metadata.name is required")

    request = {
        "operation": operation,
        "manager_url": "${CFY_MANAGER_URL}",
        "username": "${CFY_USERNAME}",
        "password": "${CFY_PASSWORD}",
        "tenant": manager.get("tenant", "${CFY_TENANT}"),
        "api_version": "${CFY_API_VERSION:-v3.1}",
        "insecure": "${CFY_INSECURE:-true}",
        "blueprint_id": blueprint_id,
        "deployment_id": deployment_id,
        "blueprint_dir": blueprint.get("source", ""),
        "application_file": blueprint.get("application_file", "blueprint.yaml"),
        "inputs_files": deployment.get("inputs", []),
        "inputs": deployment.get("inline_inputs", {}),
        "workflow": lifecycle_cfg.get("workflow", operation),
        "wait": lifecycle_cfg.get("wait", True),
        "request_timeout_sec": execution.get("request_timeout_sec", 60),
        "execution_timeout_sec": lifecycle_cfg.get("timeout_sec", execution.get("execution_timeout_sec", 3600)),
        "poll_interval_sec": execution.get("poll_interval_sec", 10),
        "retry_count": execution.get("retry_count", 5),
        "retry_backoff_sec": execution.get("retry_backoff_sec", 5),
        "delete_deployment": lifecycle_cfg.get("delete_deployment", operation == "uninstall"),
        "delete_blueprint": lifecycle_cfg.get("delete_blueprint", False),
        "dry_run": body.get("dry_run", False),
        "log_level": logging_cfg.get("level", "INFO"),
        "log_dir": logging_cfg.get("log_dir", "logs"),
    }
    return request


def expand_env_vars(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: expand_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [expand_env_vars(v) for v in obj]
    if isinstance(obj, str):
        # Supports ${VAR} and ${VAR:-default}
        import re
        pattern = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(:-([^}]*))?\}")
        def repl(match):
            name = match.group(1)
            default = match.group(3) or ""
            return _strip(os.getenv(name, default))
        return pattern.sub(repl, obj).strip()
    return obj


def write_request(request: Dict[str, Any], temp_dir: Path, deployment_id: str, operation: str) -> Path:
    path = temp_dir / f"{deployment_id}-{operation}.request.yaml"
    path.write_text(yaml.safe_dump(expand_env_vars(request), sort_keys=False), encoding="utf-8")
    return path


def execute_request(repo: Path, request_path: Path, logger: logging.Logger) -> int:
    cmd = [sys.executable, "scripts/cloudify_lifecycle.py", "--request", str(request_path)]
    logger.info("Executing: %s", " ".join(cmd))
    process = subprocess.run(cmd, cwd=str(repo), text=True)
    return process.returncode


def reconcile(repo: Path, before: str, after: str, mode: str, dry_run: bool, logger: logging.Logger) -> int:
    all_changes = get_changed_files(repo, before, after)
    changes = get_changed_deployment_files(repo, before, after)
    handled_paths = {path for _, path in changes}
    dependency_updates = discover_dependency_update_deployments(repo, all_changes, handled_paths, logger)
    changes.extend(dependency_updates)

    if not changes:
        logger.info("No deployment desired-state changes or referenced blueprint/input changes detected. Nothing to reconcile.")
        return 0

    if mode == "first" and len(changes) > 1:
        changes = changes[:1]
    elif mode == "fail" and len(changes) > 1:
        raise RuntimeError(f"Multiple deployment changes detected but GITOPS_MULTI_DEPLOYMENT_MODE=fail: {changes}")

    logger.info("Deployment reconcile actions: %s", changes)
    temp_dir = Path(tempfile.mkdtemp(prefix="cfy-gitops-requests-"))
    failures = 0
    summary = []

    for status, rel_path in changes:
        logger.info("Reconciling %s status=%s", rel_path, status)
        if status == "D":
            spec = load_yaml_text(previous_file_content(repo, before, rel_path), f"{before}:{rel_path}")
            operation = "uninstall"
        elif status in {"A", "C", "R"}:
            spec = load_yaml_file(repo / rel_path)
            operation = "install"
        elif status == "M":
            spec = load_yaml_file(repo / rel_path)
            # Optional explicit force operation for rare cases.
            operation = _strip((spec.get("spec") or {}).get("force_operation") or "update").lower()
            if operation not in {"install", "update", "uninstall"}:
                raise ValueError(f"Invalid force_operation in {rel_path}: {operation}")
        else:
            logger.info("Ignoring unsupported git status %s for %s", status, rel_path)
            continue

        request = normalize_deployment_spec(spec, operation, repo)
        deployment_id = request["deployment_id"]
        if dry_run:
            request["dry_run"] = True
        request_path = write_request(request, temp_dir, deployment_id, operation)
        logger.info("Generated lifecycle request: %s", request_path)
        logger.info("Request summary: operation=%s deployment_id=%s blueprint_id=%s", operation, deployment_id, request.get("blueprint_id"))
        rc = execute_request(repo, request_path, logger)
        summary.append({"path": rel_path, "status": status, "operation": operation, "deployment_id": deployment_id, "returncode": rc})
        if rc != 0:
            failures += 1

    (repo / "logs").mkdir(exist_ok=True)
    summary_file = repo / "logs" / "gitops-reconcile-summary.json"
    summary_file.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    logger.info("Reconcile summary written to %s", summary_file)
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile Cloudify deployment desired-state from Git diff")
    parser.add_argument("--before", required=True, help="Before Git SHA")
    parser.add_argument("--after", required=True, help="After Git SHA")
    parser.add_argument("--mode", default=os.getenv("GITOPS_MULTI_DEPLOYMENT_MODE", "all"), choices=["all", "first", "fail"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo = Path.cwd()
    run_id = uuid.uuid4().hex[:12]
    logger = setup_logging(repo / "logs", run_id, os.getenv("GITOPS_LOG_LEVEL", "INFO"))
    logger.info("GitOps reconcile run_id=%s before=%s after=%s mode=%s", run_id, args.before, args.after, args.mode)
    try:
        return reconcile(repo, args.before, args.after, args.mode, args.dry_run, logger)
    except Exception as exc:  # noqa: BLE001
        logger.exception("GitOps reconcile failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
