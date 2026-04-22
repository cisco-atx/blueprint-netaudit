"""
Route definitions for Flask application.

This module defines all application routes and maps URL rules to their
corresponding view functions. It integrates authentication and
authorization decorators for protected endpoints.

File path: routes/__init__.py
"""

from flask import redirect, url_for, current_app

# Local application imports
from .api import (
    delete_dataset_items,
    get_dataset,
    get_device_results,
    save_dataset_item,
    save_device_results,
    save_device_results_util,
    save_followup,
)
from .check import (
    check_git_repo_status,
    clone_git_repo,
    delete_git_repo,
    export_checks,
    generate_check,
    prepare_test,
    pull_git_repo,
    run_handler,
    scan_checks,
    scan_git_repos,
)
from .dashboard import render_dashboard
from .manage import (
    render_manage_checks,
    render_manage_connectors,
    render_manage_devices,
    render_manage_views,
)
from .quickaudit import (
    export_report,
    quickaudit_report,
    quickaudit_run,
    render_quickaudit,
)
from .results import (
    get_results_for_view,
    render_results_for_device,
    render_results_for_views,
    results_run,
    snap_results_for_devices,
)


def redirect_root():
    """Redirect root URL to dashboard."""
    return redirect(url_for("netaudit.render_dashboard"))


routes = [
    {
        "rule": "/",
        "endpoint": "redirect_root",
        "view_func": redirect_root,
        "methods": ["GET"],
    },
    {
        "rule": "/dashboard",
        "endpoint": "render_dashboard",
        "view_func": current_app.routes.login_required(
            render_dashboard
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/results/views",
        "endpoint": "render_results_for_views",
        "view_func": current_app.routes.login_required(
            render_results_for_views
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/results/view/<view_name>",
        "endpoint": "get_results_for_view",
        "view_func": current_app.routes.login_required(
            get_results_for_view
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/results/device/<device_id>",
        "endpoint": "render_results_for_device",
        "view_func": current_app.routes.login_required(
            render_results_for_device
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/results/snap",
        "endpoint": "snap_results_for_devices",
        "view_func": current_app.routes.login_required(
            snap_results_for_devices
        ),
        "methods": ["POST"],
    },
    {
        "rule": "/results/run",
        "endpoint": "results_run",
        "view_func": current_app.routes.login_required(
            results_run
        ),
        "methods": ["POST"],
    },
    {
        "rule": "/quickaudit",
        "endpoint": "render_quickaudit",
        "view_func": current_app.routes.login_required(
            render_quickaudit
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/quickaudit/run",
        "endpoint": "quickaudit_run",
        "view_func": current_app.routes.login_required(
            quickaudit_run
        ),
        "methods": ["POST"],
    },
    {
        "rule": "/quickaudit/report",
        "endpoint": "quickaudit_report",
        "view_func": current_app.routes.login_required(
            quickaudit_report
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/quickaudit/export",
        "endpoint": "export_report",
        "view_func": current_app.routes.login_required(
            export_report
        ),
        "methods": ["POST"],
    },
    {
        "rule": "/api/<dataset>",
        "endpoint": "api_get_dataset",
        "view_func": current_app.routes.login_required(
            get_dataset
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/api/<dataset>",
        "endpoint": "api_delete_dataset_items",
        "view_func": current_app.routes.login_required(
            delete_dataset_items
        ),
        "methods": ["DELETE"],
    },
    {
        "rule": "/api/<dataset>",
        "endpoint": "api_save_dataset_item",
        "view_func": current_app.routes.login_required(
            save_dataset_item
        ),
        "methods": ["POST"],
    },
    {
        "rule": "/api/results/<device_id>",
        "endpoint": "api_get_device_results",
        "view_func": current_app.routes.login_required(
            get_device_results
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/api/results/<device_id>",
        "endpoint": "api_save_device_results",
        "view_func": current_app.routes.login_required(
            save_device_results
        ),
        "methods": ["POST"],
    },
    {
        "rule": "/api/results/followup",
        "endpoint": "api_save_followup",
        "view_func": current_app.routes.login_required(
            save_followup
        ),
        "methods": ["POST"],
    },
    {
        "rule": "/api/checks/scan",
        "endpoint": "api_scan_checks",
        "view_func": current_app.routes.admin_required(
            scan_checks
        ),
        "methods": ["POST"],
    },
    {
        "rule": "/api/checks/export",
        "endpoint": "api_export_checks",
        "view_func": current_app.routes.admin_required(
            export_checks
        ),
        "methods": ["POST"],
    },
    {
        "rule": "/api/checks/generate",
        "endpoint": "api_generate_check",
        "view_func": current_app.routes.admin_required(
            generate_check
        ),
        "methods": ["POST"],
    },
    {
        "rule": "/manage/views",
        "endpoint": "render_manage_views",
        "view_func": current_app.routes.admin_required(
            render_manage_views
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/manage/devices",
        "endpoint": "render_manage_devices",
        "view_func": current_app.routes.admin_required(
            render_manage_devices
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/manage/checks",
        "endpoint": "render_manage_checks",
        "view_func": current_app.routes.admin_required(
            render_manage_checks
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/manage/connectors",
        "endpoint": "render_manage_connectors",
        "view_func": current_app.routes.admin_required(
            render_manage_connectors
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/manage/checks/scan_repos",
        "endpoint": "check_scan_git_repos",
        "view_func": current_app.routes.admin_required(
            scan_git_repos
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/manage/checks/check_repo_status",
        "endpoint": "check_git_repo_status",
        "view_func": current_app.routes.admin_required(
            check_git_repo_status
        ),
        "methods": ["POST"],
    },
    {
        "rule": "/manage/checks/clone_repo",
        "endpoint": "check_clone_git_repo",
        "view_func": current_app.routes.admin_required(
            clone_git_repo
        ),
        "methods": ["POST"],
    },
    {
        "rule": "/manage/checks/sync_repo",
        "endpoint": "check_pull_git_repo",
        "view_func": current_app.routes.admin_required(
            pull_git_repo
        ),
        "methods": ["POST"],
    },
    {
        "rule": "/manage/checks/delete_repo",
        "endpoint": "check_delete_git_repo",
        "view_func": current_app.routes.admin_required(
            delete_git_repo
        ),
        "methods": ["POST"],
    },
    {
        "rule": "/check/prepare_test",
        "endpoint": "check_prepare_test",
        "view_func": current_app.routes.admin_required(
            prepare_test
        ),
        "methods": ["POST"],
    },
    {
        "rule": "/check/run_handler",
        "endpoint": "check_run_handler",
        "view_func": current_app.routes.admin_required(
            run_handler
        ),
        "methods": ["POST"],
    },
]
