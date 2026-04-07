from flask import render_template, current_app, url_for
from datetime import datetime
from collections import defaultdict


def render_dashboard():
    """Render the NetAudit Dashboard page with KPIs, user actions, donut charts, and timeline data."""
    netaudit_bp = current_app.blueprints.get("netaudit")

    views = dict(netaudit_bp.views_db)
    devices = dict(netaudit_bp.devices_db)

    # Initialize data for template rendering
    kwargs = {
        "breadcrumbs": [
            {"title": "NetAudit", "url": url_for("netaudit.render_dashboard")},
            {"title": "Dashboard"}
        ],
        "views": views,
        "devices": {
            "total_devices": len(devices),
            "passed_devices": 0,
            "failed_devices": 0,
            "unknown_devices": 0
        },
        "user_actions": {},
        "donut_data": {"pass": {}, "fail": {}},
        "timeline_data": defaultdict(dict)
    }

    # Setup initial user action structure with icons and colors
    inventory_user_actions = netaudit_bp.constants.USER_ACTIONS
    for action, action_data in inventory_user_actions.items():
        kwargs["user_actions"][action] = {
            "count": 0,
            "icon": action_data["icon"],
            "color": action_data["color"],
        }

    # Iterate over devices to populate KPIs, user actions, donut chart, and timeline data
    for hostname, device_info in devices.items():
        # Fetch device analysis results

        device_data = netaudit_bp.routes.get_device_results(hostname).get_json()
        views_for_device = device_info.get("view", ["Unknown"])
        status = device_data.get("status", 0)

        # Calculate Key Performance Indicators (KPIs)
        if status == 1:  # PASS
            kwargs["devices"]["passed_devices"] += 1
        elif status == 2:  # FAIL
            kwargs["devices"]["failed_devices"] += 1
        else:  # NOT_RUN, WARN, INFO, ERROR, INCONCLUSIVE
            kwargs["devices"]["unknown_devices"] += 1

        # Count user actions
        user_action = device_data.get("user_action", "")
        if not user_action and status == 2:
            user_action = "Action Required"
        if user_action in kwargs["user_actions"]:
            kwargs["user_actions"][user_action]["count"] += 1

        # Update donut chart and timeline for all views
        date_added = device_info.get("date")
        for view_name in views_for_device:
            # Donut chart
            kwargs["donut_data"]["pass"].setdefault(view_name, 0)
            kwargs["donut_data"]["fail"].setdefault(view_name, 0)
            if status == 1:  # PASS
                kwargs["donut_data"]["pass"][view_name] += 1
            elif status == 2:  # FAIL
                kwargs["donut_data"]["fail"][view_name] += 1

            # Timeline
            if date_added:
                try:
                    dt = datetime.fromisoformat(date_added)
                    month_label = dt.strftime("%b %Y")
                except ValueError:
                    month_label = date_added
                kwargs["timeline_data"].setdefault(view_name, {}).setdefault(month_label, 0)
                kwargs["timeline_data"][view_name][month_label] += 1

    # Convert defaultdict to regular dict for compatibility with templates
    kwargs["timeline_data"] = dict(kwargs["timeline_data"])

    return render_template("netaudit.dashboard.html", **kwargs)