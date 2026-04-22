"""Dashboard routes for NetAudit application.

This module handles rendering of the NetAudit dashboard, including
aggregation of KPIs, user actions, donut chart data, and timeline data.
It processes device results and prepares structured data for templates.

File path: routes/dashboard.py
"""

import logging
from collections import defaultdict
from datetime import datetime

from flask import current_app, render_template, url_for

logger = logging.getLogger(__name__)


def render_dashboard():
    """Render the NetAudit Dashboard page with aggregated metrics."""
    netaudit_bp = current_app.blueprints.get("netaudit")

    views = dict(netaudit_bp.views_db)
    devices = dict(netaudit_bp.devices_db)

    kwargs = {
        "breadcrumbs": [
            {"title": "NetAudit",
             "url": url_for("netaudit.render_dashboard")},
            {"title": "Dashboard"},
        ],
        "views": views,
        "devices": {
            "total_devices": len(devices),
            "passed_devices": 0,
            "failed_devices": 0,
            "unknown_devices": 0,
        },
        "user_actions": {},
        "donut_data": {"pass": {}, "fail": {}},
        "timeline_data": defaultdict(dict),
    }

    inventory_user_actions = netaudit_bp.constants.USER_ACTIONS
    for action, action_data in inventory_user_actions.items():
        kwargs["user_actions"][action] = {
            "count": 0,
            "icon": action_data["icon"],
            "color": action_data["color"],
        }

    for hostname, device_info in devices.items():
        try:
            device_response = netaudit_bp.routes.get_device_results(
                hostname
            )
            device_data = device_response.get_json()
        except Exception:
            logger.exception(
                "Failed to fetch device results for %s", hostname
            )
            continue

        views_for_device = device_info.get("view", ["Unknown"])
        status = device_data.get("status", 0)

        if status == 1:
            kwargs["devices"]["passed_devices"] += 1
        elif status == 2:
            kwargs["devices"]["failed_devices"] += 1
        else:
            kwargs["devices"]["unknown_devices"] += 1

        user_action = device_data.get("user_action", "")
        if not user_action and status == 2:
            user_action = "Action Required"

        if user_action in kwargs["user_actions"]:
            kwargs["user_actions"][user_action]["count"] += 1

        date_added = device_info.get("date")

        for view_name in views_for_device:
            kwargs["donut_data"]["pass"].setdefault(view_name, 0)
            kwargs["donut_data"]["fail"].setdefault(view_name, 0)

            if status == 1:
                kwargs["donut_data"]["pass"][view_name] += 1
            elif status == 2:
                kwargs["donut_data"]["fail"][view_name] += 1

            if date_added:
                try:
                    dt = datetime.fromisoformat(date_added)
                    month_label = dt.strftime("%b %Y")
                except ValueError:
                    logger.warning(
                        "Invalid date format for device %s: %s",
                        hostname,
                        date_added,
                    )
                    month_label = date_added

                timeline_view = kwargs["timeline_data"].setdefault(view_name, {})
                timeline_view[month_label] = (
                        timeline_view.get(month_label, 0) + 1
                )

    kwargs["timeline_data"] = dict(kwargs["timeline_data"])

    return render_template("netaudit.dashboard.html", **kwargs)
