import logging
import datetime
import copy
import os
from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO
from flask import current_app, render_template, url_for, jsonify, request, make_response

def render_results_for_views():
    netaudit_bp = current_app.blueprints.get("netaudit")
    views = dict(netaudit_bp.views_db)

    kwargs = {
        "breadcrumbs": [
            {"title": "NetAudit", "url": url_for("netaudit.render_dashboard")},
            {"title": "Results"}
        ],
        "views": [
            {
                "name": name,
                "icon": data.get("icon", "table_rows")
            }
        for name, data in views.items()
        ],
        "std_user_actions": netaudit_bp.constants.USER_ACTIONS,
        "status_codes": netaudit_bp.constants.AUDIT_STATUS_CODES,
    }
    return render_template("netaudit.results.html", **kwargs)

def get_results_for_view(view_name):
    netaudit_bp = current_app.blueprints.get("netaudit")

    views = dict(netaudit_bp.views_db)
    checks = dict(netaudit_bp.checks_db)

    view_devices = views.get(view_name, {}).get("devices", [])
    view_checks = views.get(view_name, {}).get("checks", [])

    columns = ["Hostname", "Overall", "Action Taken"] + [
        checks.get(chk, {}).get("name", chk)
        for chk in view_checks
    ]

    rows = []

    for device_id in view_devices:
        device_data = netaudit_bp.routes.get_device_results(device_id).get_json()

        row = {
            "device_id": device_id,
            "hostname": device_data.get("hostname"),
            "overall": device_data.get("status"),
            "action_taken": device_data.get("user_action"),
            "last_audit": datetime.datetime.fromisoformat(
                device_data.get("last_audit", "0001-01-01T00:00.000000").split(".")[0]
            ).strftime("%d-%b-%Y %H:%M"),
            "checks": [
                device_data.get("checks", {}).get(chk, {}).get("status", 0)
                for chk in view_checks
            ]
        }
        rows.append(row)

    return jsonify({
        "columns": columns,
        "rows": rows
    })


def render_results_for_device(device_id):
    """
    Render the audit results for a specific device.

    Parameters:
        device_id (str): The ID of the device for which audit results are rendered.

    Returns:
        str: The rendered HTML template.
    """
    return render_template("netaudit.results.device.html", **get_results_for_device(device_id))


def snap_results_for_devices():
    """
    Generate a snapshot HTML report for a specific device's audit results.
    """
    netaudit_bp = current_app.blueprints.get("netaudit")
    payload = request.get_json()
    device_ids = payload.get("device_ids", [])

    if not device_ids:
        return {"error": "No devices provided"}, 400

    def get_static_file(path):
        current_app_static_folder = current_app.static_folder
        netaudit_static_folder = netaudit_bp.static_folder

        content = ""
        if os.path.exists(os.path.join(current_app_static_folder, path)):
            with open(os.path.join(current_app_static_folder, path), "r") as f:
                content += f.read()
        if os.path.exists(os.path.join(netaudit_static_folder, path)):
            with open(os.path.join(netaudit_static_folder, path), "r") as f:
                content += f.read()

        return content


    generated_at = datetime.datetime.now()
    ts = generated_at.strftime("%Y-%m-%d_%H.%M")
    zip_filename = f"Audit_Results_{ts}.zip"

    zip_buffer = BytesIO()

    with ZipFile(zip_buffer, "w", ZIP_DEFLATED) as zipf:
        for device_id in device_ids:
            html_filename = f"Audit Results_{device_id}_{ts}.html"

            html = render_template(
                "netaudit.results.snap.html",
                **get_results_for_device(device_id),
                embed_local_assets=True,
                get_static_file=get_static_file,
                report_filename=html_filename,
                generated_at=generated_at
            )

            zipf.writestr(html_filename, html)

    zip_buffer.seek(0)

    response = make_response(zip_buffer.read())
    response.headers["Content-Type"] = "application/zip"
    response.headers["Content-Disposition"] = (
        f"attachment; filename={zip_filename}"
    )
    return response

def get_results_for_device(device_id):
    """
    Prepare the context for rendering audit results for a specific device.

    Parameters:
        device_id (str): The ID of the device.
    Returns:
        dict: Context dictionary for rendering.
    """
    netaudit_bp = current_app.blueprints.get("netaudit")
    view = request.args.get("view")

    device_data = netaudit_bp.routes.get_device_results(device_id).get_json()

    view = view or next(iter(dict(netaudit_bp.views_db)))

    kwargs = {
        "columns": ["Check Name", "Status", "Observation", "Comments"],
        "breadcrumbs": [
            {"title": "NetAudit", "url": url_for("netaudit.render_dashboard")},
            {"title": "Results",
             "url": url_for("netaudit.render_results_for_views")},
            {"title": device_data.get("hostname", device_id)}
        ],
        "device_id": device_id,
        "device_data": device_data,
        "std_user_actions": netaudit_bp.constants.USER_ACTIONS,
        "status_codes": netaudit_bp.constants.AUDIT_STATUS_CODES,
        "view": view,
        "date_added": datetime.datetime.fromisoformat(netaudit_bp.devices_db.get(device_id, {}).get("date", "").split(".")[0]).strftime(
            "%d-%b-%Y %H:%M"
        ),
        "last_audit": datetime.datetime.fromisoformat(
            device_data.get("last_audit", "0001-01-01T00:00.000000").split(".")[0]
        ).strftime("%d-%b-%Y %H:%M"),
    }

    dataset = []
    view_checks = netaudit_bp.views_db.get(view, {}).get("checks", [])
    check_data = device_data.get("checks", {})
    for check in view_checks:
        dataset.append({
            "Check Name": netaudit_bp.checks_db.get(check, {}).get("name", check),
            "Status": check_data.get(check, {}).get("status", 0),
            "Observation": check_data.get(check, {}).get("observation", ""),
            "Comments": "\n".join(check_data.get(check, {}).get("comments", []))
        })

    kwargs["dataset"] = dataset

    return kwargs


def results_run():
    netaudit_bp = current_app.blueprints.get("netaudit")
    data = request.get_json()
    device_data = data.get("devices", {})
    view = data.get("view", None)

    devices = []

    for device_id, connector in device_data.items():
        check_list = netaudit_bp.views_db.get(view, {}).get("checks", []) if view else []

        devices.append({
            "device": device_id,
            "check_list": check_list,
            "connector": connector,
        })

    context = {}

    audit_service = netaudit_bp.services.AuditService(
        devices, netaudit_bp.CHECKS_DIR, netaudit_bp.FACTS_DIR, context=context
    )

    audit_service.start_thread_executor()
    audit_service.wait_for_completion()

    for device_id, results in audit_service.results.items():
        netaudit_bp.routes.save_device_results_util(device_id, results)
        logging.info(f"Audit results written for device '{device_id}'")

    return jsonify({"success": True, "message": "Audit completed"}), 200