"""Check routes for managing network device tests and Git operations.

Provides endpoints to scan, export, generate, and test network checks,
as well as manage Git repositories within the checks directory.

File path: routes/check.py
"""

import io
import logging
import os
import shutil
import stat
import subprocess
import sys
import traceback
import zipfile
import importlib.util

from flask import current_app, jsonify, request, send_file, session

# Runtime in-memory store for active checks (per browser session)
CHECK_TEST_SESSIONS = {}

logger = logging.getLogger(__name__)


def scan_checks():
    """Scan check scripts and return metadata."""
    netaudit_bp = current_app.blueprints.get("netaudit")
    checks_dir = netaudit_bp.CHECKS_DIR
    checks = {}

    for root, _, files in os.walk(checks_dir):
        for filename in files:
            if not filename.endswith(".py") or filename.startswith("__"):
                continue

            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, checks_dir)
            module_name = rel_path.replace(os.sep, "_").replace(".py", "")

            spec = importlib.util.spec_from_file_location(
                module_name, file_path
            )
            module = importlib.util.module_from_spec(spec)

            try:
                spec.loader.exec_module(module)
            except Exception as exc:
                logger.warning(
                    "Skipping %s: import error: %s", rel_path, exc
                )
                continue

            check_class = getattr(module, "CHECK_CLASS", None)
            if not check_class:
                logger.warning(
                    "Skipping %s: CHECK_CLASS not found", rel_path
                )
                continue

            metadata = {
                "name": getattr(check_class, "NAME", ""),
                "version": getattr(check_class, "VERSION", ""),
                "tags": getattr(check_class, "TAGS", []),
                "description": getattr(check_class, "DESCRIPTION", ""),
                "complexity": getattr(check_class, "COMPLEXITY", 1),
                "author": getattr(check_class, "AUTHOR", "Unknown"),
            }

            with open(file_path, "r", encoding="utf-8") as file:
                metadata["code"] = file.read()

            checks[rel_path] = metadata

    netaudit_bp.checks_db.update(checks)
    return jsonify(checks)


def export_checks():
    """Export selected checks as a ZIP file."""
    netaudit_bp = current_app.blueprints.get("netaudit")
    payload = request.get_json()
    selected_checks = payload.get("checks", [])
    checks_dir = netaudit_bp.CHECKS_DIR

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(
            zip_buffer, "w", zipfile.ZIP_DEFLATED
    ) as zip_file:
        for check_filename in selected_checks:
            file_path = os.path.join(checks_dir, check_filename)
            if os.path.exists(file_path):
                zip_file.write(file_path, arcname=check_filename)

    logger.info("Exported %d checks", len(selected_checks))
    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="exported_checks.zip",
    )


def generate_check():
    """Generate a check script using AI."""
    netaudit_bp = current_app.blueprints.get("netaudit")
    data = request.json
    description = data.get("description")
    sample_output = data.get("sampleOutput", "")

    user_prompt = (
        netaudit_bp.checkprompt.CHECK_PROMPT_TEMPLATE
        .replace("<INSERT_DESCRIPTION_HERE>", description)
        .replace("<INSERT_SAMPLE_OUTPUT_HERE>", sample_output)
    )

    if current_app.azureai.is_ready:
        try:
            logger.info("Generating check via AI")
            code = current_app.azureai.ask(
                system_prompt=(
                    "You are a Python developer generating a Netaudit check."
                ),
                user_prompt=user_prompt,
                format="code",
            )
            return jsonify({"status": "success", "code": code})
        except Exception as exc:
            logger.exception("AI generation failed")
            return jsonify(
                {"status": "error", "message": str(exc)}
            ), 500

    logger.warning("AI client not configured")
    return jsonify(
        {"status": "error", "message": "AI client not configured."}
    )


def safe_exec_check(code: str):
    """Execute check code and return CHECK_CLASS."""
    local_env = {}
    sys_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        exec(code, local_env)
    finally:
        sys.stdout = sys_stdout

    cls = local_env.get("CHECK_CLASS")
    if not cls:
        raise ValueError("CHECK_CLASS not defined in provided code")

    return cls


def prepare_test():
    """Prepare a test session for a check."""
    data = request.get_json()
    code = data.get("code", "")

    if not code.strip():
        return jsonify({"error": "Empty check code"}), 400

    try:
        cls = safe_exec_check(code)
        context = {"flask": current_app}
        check = cls(device="TestDevice", context=context)

        session_id = str(id(check))
        CHECK_TEST_SESSIONS[session_id] = check
        session["test_session_id"] = session_id

        return jsonify(
            {
                "session_id": session_id,
                "requests": check.REQUESTS,
                "results": check.RESULTS,
            }
        )
    except Exception:
        logger.exception("Failed to prepare test session")
        return jsonify({"error": traceback.format_exc()}), 500


def run_handler():
    """Run handler for the current test session."""
    data = request.get_json()
    sample_output = data.get("sample_output", "")

    session_id = session.get("test_session_id")
    if not session_id:
        return jsonify(
            {"error": "Test session expired or missing"}
        ), 400

    check = CHECK_TEST_SESSIONS.get(session_id)
    if not check:
        return jsonify(
            {"error": "Test session expired or missing"}
        ), 400

    try:
        handler_name = check.REQUESTS.get("handler")
        if not handler_name:
            return jsonify(
                {"error": "No handler defined in REQUESTS"}
            ), 400

        if not hasattr(check, handler_name):
            return jsonify(
                {"error": f"Handler '{handler_name}' not found"}
            ), 400

        handler = getattr(check, handler_name)
        req = check.REQUESTS

        handler(req["device"], req["command"], sample_output)

        return jsonify(
            {
                "session_id": session_id,
                "results": check.RESULTS,
                "requests": check.REQUESTS,
            }
        )
    except Exception:
        logger.exception("Handler execution failed")
        return jsonify({"error": traceback.format_exc()}), 500


def scan_git_repos():
    """Scan directory for Git repositories."""
    netaudit_bp = current_app.blueprints.get("netaudit")
    git_repos = []

    for root, dirs, _ in os.walk(netaudit_bp.CHECKS_DIR):
        if ".git" in dirs:
            try:
                remote_url = subprocess.check_output(
                    [
                        "git",
                        "-C",
                        root,
                        "config",
                        "--get",
                        "remote.origin.url",
                    ],
                    text=True,
                ).strip()
            except subprocess.CalledProcessError:
                remote_url = ""

            git_repos.append(
                {"local_path": root, "remote_url": remote_url}
            )
            dirs.remove(".git")

    return jsonify(git_repos), 200


def check_git_repo_status():
    """Check if repository is behind origin/master."""
    netaudit_bp = current_app.blueprints.get("netaudit")
    data = request.get_json()
    local_path = data.get("local_path", "").strip()

    if not local_path:
        return jsonify({"error": "Repository path is required"}), 400

    full_path = os.path.join(netaudit_bp.CHECKS_DIR, local_path)

    if not os.path.isdir(os.path.join(full_path, ".git")):
        return jsonify({"error": "Not a Git repository"}), 400

    try:
        subprocess.check_output(
            ["git", "fetch"],
            cwd=full_path,
            text=True,
            stderr=subprocess.STDOUT,
        )

        result = subprocess.check_output(
            [
                "git",
                "rev-list",
                "--left-right",
                "--count",
                "master...origin/master",
            ],
            cwd=full_path,
            text=True,
        ).strip()

        _, behind = map(int, result.split())
        return jsonify({"update_available": behind > 0})

    except subprocess.CalledProcessError as exc:
        logger.error("Git status check failed: %s", exc.output)
        return jsonify(
            {"error": "Git error", "details": exc.output}
        ), 500


def pull_git_repo():
    """Pull latest changes for a Git repository."""
    netaudit_bp = current_app.blueprints.get("netaudit")
    data = request.get_json()
    local_path = data.get("local_path", "").strip()

    if not local_path:
        return jsonify({"error": "Repository path is required"}), 400

    if not os.path.isdir(os.path.join(local_path, ".git")):
        return jsonify(
            {"error": "Specified path is not a Git repository"}
        ), 400

    try:
        output = subprocess.check_output(
            ["git", "pull"],
            cwd=local_path,
            text=True,
            stderr=subprocess.STDOUT,
        )

        netaudit_bp.checks_db.clear()
        netaudit_bp.checks_db = (
            netaudit_bp.routes.scan_checks().get_json()
        )

        return jsonify(
            {"message": f"Successfully pulled updates:\n{output}"}
        ), 200

    except subprocess.CalledProcessError as exc:
        logger.error("Git pull failed: %s", exc.output)
        return jsonify(
            {"error": f"Git pull failed: {exc.output}"}
        ), 500


def clone_git_repo():
    """Clone a Git repository."""
    netaudit_bp = current_app.blueprints.get("netaudit")
    data = request.get_json()
    remote_url = data.get("remote_url", "").strip()
    local_repo_name = data.get("local_repo_name", "").strip()

    if not remote_url:
        return jsonify({"error": "Repository URL is required"}), 400

    try:
        subprocess.check_output(
            ["git", "clone", remote_url, local_repo_name],
            cwd=netaudit_bp.CHECKS_DIR,
            text=True,
            stderr=subprocess.STDOUT,
        )

        netaudit_bp.checks_db.clear()
        netaudit_bp.checks_db = (
            netaudit_bp.routes.scan_checks().get_json()
        )

        logger.info("Cloned repository %s", remote_url)
        return jsonify(
            {"message": f"Successfully cloned {remote_url}"}
        ), 200

    except subprocess.CalledProcessError as exc:
        logger.error("Git clone failed: %s", exc.output)
        return jsonify(
            {"error": f"Git clone failed: {exc.output}"}
        ), 500


def delete_git_repo():
    """Delete a Git repository safely."""

    def _remove_readonly(func, path, _):
        """Remove read-only attribute and retry."""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    netaudit_bp = current_app.blueprints.get("netaudit")
    data = request.get_json()
    local_path = data.get("local_path", "").strip()

    if not local_path:
        return jsonify({"error": "Repository path is required"}), 400

    if not os.path.isdir(local_path):
        return jsonify(
            {"error": "Specified path does not exist"}
        ), 400

    try:
        shutil.rmtree(local_path, onerror=_remove_readonly)

        netaudit_bp.checks_db.clear()
        netaudit_bp.checks_db = (
            netaudit_bp.routes.scan_checks().get_json()
        )

        logger.info("Deleted repository %s", local_path)
        return jsonify(
            {
                "message": (
                    f"Successfully deleted repository at {local_path}"
                )
            }
        ), 200

    except Exception as exc:
        logger.exception("Failed to delete repository")
        return jsonify(
            {"error": f"Failed to delete repository: {str(exc)}"}
        ), 500
