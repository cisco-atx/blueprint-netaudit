"""Management views rendering module.

Provides functions to render management pages for views, devices,
checks, and connectors in the Flask application.

File path: routes/manage.py
"""

from datetime import datetime
import logging

from flask import current_app, render_template, url_for

logger = logging.getLogger(__name__)


def render_manage_views():
    """Render the 'Manage Views' page."""

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
        "view_icons": netaudit_bp.constants.VIEW_ICONS,
    }

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
        dataset.append(
            {
                "Name": name,
                "Icon": view_data.get("icon"),
                "Checks": checks_list,
            }
        )

    kwargs["dataset"] = dataset

    return render_template("netaudit.manage.views.html", **kwargs)


def render_manage_devices():
    """Render the 'Manage Devices' page."""

    netaudit_bp = current_app.blueprints.get("netaudit")

    dataset = []
    for hostname, data in netaudit_bp.devices_db.items():
        try:
            date_str = data.get("date", "").split(".")[0]
            formatted_date = datetime.fromisoformat(date_str).strftime(
                "%d-%b-%Y %H:%M"
            )
        except (ValueError, TypeError) as exc:
            logger.warning(
                "Invalid date format for device %s: %s", hostname, exc
            )
            formatted_date = "Invalid Date"

        dataset.append(
            {
                "Hostname": hostname,
                "View(s)": ", ".join(data.get("view", [])),
                "Connector": data.get("connector", ""),
                "Date Added": formatted_date,
                "Created By": data.get("user", ""),
            }
        )

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
        "dataset": dataset,
        "breadcrumbs": [
            {"title": "NetAudit", "url": url_for("netaudit.render_dashboard")},
            {"title": "Devices"},
        ],
        "fields": ["Hostname", "Device Type", "View", "Connector"],
        "connectors": list(netaudit_bp.connectors_db.keys()),
        "view_list": list(netaudit_bp.views_db.keys()),
    }

    return render_template("netaudit.manage.devices.html", **kwargs)


def render_manage_checks():
    """Render the 'Manage Checks' page."""

    netaudit_bp = current_app.blueprints.get("netaudit")

    dataset = [
        {
            "Name": chk.get("name", "Unnamed Check"),
            "Filepath": filename,
            "Description": chk.get(
                "description", "No description available."
            ),
            "Author": chk.get("author", "Unknown").strip(),
        }
        for filename, chk in netaudit_bp.checks_db.items()
    ]

    kwargs = {
        "add_text": "Add Check",
        "add_icon": "add_task",
        "columns": ["Filepath", "Name", "Description", "Author"],
        "dataset": dataset,
        "breadcrumbs": [
            {"title": "NetAudit", "url": url_for("netaudit.render_dashboard")},
            {"title": "Checks"},
        ],
        "ai_client_ready": current_app.azureai.is_ready(),
        "status_codes": netaudit_bp.constants.AUDIT_STATUS_CODES,
    }

    return render_template("netaudit.manage.checks.html", **kwargs)


def render_manage_connectors():
    """Render the 'Manage Connectors' page."""

    netaudit_bp = current_app.blueprints.get("netaudit")

    dataset = [
        {
            "Name": name,
            "JS Hostname": connector.get("jumphost_ip", "Unknown"),
            "JS Username": connector.get(
                "jumphost_username", "Unknown"
            ),
            "Network Username": connector.get(
                "network_username", "Unknown"
            ),
        }
        for name, connector in netaudit_bp.connectors_db.items()
    ]

    kwargs = {
        "add_text": "Add Connector",
        "add_icon": "add_link",
        "columns": [
            "Name",
            "JS Hostname",
            "JS Username",
            "Network Username",
        ],
        "dataset": dataset,
        "breadcrumbs": [
            {"title": "NetAudit", "url": url_for("netaudit.render_dashboard")},
            {"title": "Connectors"},
        ],
    }

    return render_template("netaudit.manage.connectors.html", **kwargs)
