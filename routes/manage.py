"""
Module for rendering various management views in a Flask application.
The module provides functions to render pages for managing views, devices,
checks, connectors, and users in the application.
"""

from datetime import datetime
import logging

from flask import render_template, current_app, url_for, session

def render_manage_views():
    """
    Render the 'Manage Views' page.

    Returns:
        str: Rendered HTML for the manage views page.
    """
    netaudit_bp = current_app.blueprints.get("netaudit")
    views = dict(netaudit_bp.views_db)
    checks = dict(netaudit_bp.checks_db)

    kwargs = {
        "add_text": "Add View",
        "add_icon": "list_alt_add",
        "columns": ["Name", "Checks"],
        "breadcrumbs": [
            {"title": "NetAudit", "url": url_for("netaudit.render_dashboard")},
            {"title": "Views"},
        ],
    }
    kwargs["view_icons"] = netaudit_bp.constants.VIEW_ICONS

    dataset = []
    for name, view_data in views.items():
        checks_list = [
            {
                "name": checks[chk]["name"],
                "description": checks[chk]["description"],
            }
            for chk in view_data.get("checks", [])
            if checks.get(chk)
        ]
        icon = view_data.get("icon")
        dataset.append({"Name": name, "Icon":icon, "Checks": checks_list})

    kwargs["dataset"] = dataset
    return render_template("netaudit.manage.views.html", **kwargs)


def render_manage_devices():
    """
    Render the 'Manage Devices' page.

    Returns:
        str: Rendered HTML for the manage devices page.
    """
    netaudit_bp = current_app.blueprints.get("netaudit")
    kwargs = {
        "add_text": "Add Device(s)",
        "add_icon": "add_to_queue",
        "columns": [
            "Hostname",
            "View(s)",
            "Connector",
            "Date Added",
            "Created By",
        ],
        "dataset": [
            {
                "Hostname": hostname,
                "View(s)": ", ".join(data.get("view", [])),
                "Connector": data.get("connector", ""),
                "Date Added": datetime.fromisoformat(
                    data.get("date", "").split(".")[0]
                ).strftime("%d-%b-%Y %H:%M"),
                "Created By": data.get("user", ""),
            }
            for hostname, data in netaudit_bp.devices_db.items()
        ],
        "breadcrumbs": [
            {"title": "NetAudit", "url": url_for("netaudit.render_dashboard")},
            {"title": "Devices"},
        ],
        "fields": ["Hostname", "Device Type", "View", "Connector"],
        "connectors": list(netaudit_bp.connectors_db.keys()),
        "view_list": list(netaudit_bp.views_db.keys())
    }

    return render_template("netaudit.manage.devices.html", **kwargs)


def render_manage_checks():
    """
    Render the 'Manage Checks' page.

    Returns:
        str: Rendered HTML for the manage checks page.
    """
    netaudit_bp = current_app.blueprints.get("netaudit")

    kwargs = {
        "add_text": "Add Check",
        "add_icon": "add_task",
        "columns": ["Filepath", "Name", "Description", "Author"],
        "dataset": [
            {
                "Name": chk.get("name", "Unnamed Check"),
                "Filepath": filename,
                "Description": chk.get("description", "No description available."),
                "Author": chk.get("author", "Unknown")
                .strip(),
            }
            for filename, chk in netaudit_bp.checks_db.items()
        ],
        "breadcrumbs": [
            {"title": "NetAudit", "url": url_for("netaudit.render_dashboard")},
            {"title": "Checks"},
        ],
        "ai_client_ready": current_app.azureai.is_ready(),
        "status_codes": netaudit_bp.constants.AUDIT_STATUS_CODES,
    }

    return render_template("netaudit.manage.checks.html", **kwargs)


def render_manage_connectors():
    """
    Render the 'Manage Connectors' page.

    Returns:
        str: Rendered HTML for the manage connectors page.
    """
    netaudit_bp = current_app.blueprints.get("netaudit")

    kwargs = {
        "add_text": "Add Connector",
        "add_icon": "add_link",
        "columns": ["Name", "JS Hostname", "JS Username", "Network Username"],
        "dataset": [
            {
                "Name": name,
                "JS Hostname": connector.get("jumphost_ip", "Unknown"),
                "JS Username": connector.get("jumphost_username", "Unknown"),
                "Network Username": connector.get("network_username", "Unknown"),
            }
            for name, connector in netaudit_bp.connectors_db.items()
        ],
        "breadcrumbs": [
            {"title": "NetAudit", "url": url_for("netaudit.render_dashboard")},
            {"title": "Connectors"},
        ],
    }

    return render_template("netaudit.manage.connectors.html", **kwargs)