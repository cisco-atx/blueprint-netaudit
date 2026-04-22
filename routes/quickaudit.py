"""Quick Audit routes and utilities.

Provides endpoints and helpers for rendering the Quick Audit UI,
executing audits, generating reports, and exporting results to Excel.

File path: routes/quickaudit.py
"""

import json
import os
from datetime import datetime

from flask import (
    current_app,
    jsonify,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from netcore import XLBW


def render_quickaudit():
    """Render the Quick Audit page."""
    netaudit_bp = current_app.blueprints.get("netaudit")
    checks = netaudit_bp.checks_db

    kwargs = {
        "breadcrumbs": [
            {"title": "NetAudit", "url": url_for("netaudit.redirect_root")},
            {"title": "Quick Audit"},
        ],
        "checks": checks,
        "status_codes": netaudit_bp.constants.AUDIT_STATUS_CODES,
    }

    return render_template("netaudit.quickaudit.html", **kwargs)


def quickaudit_run():
    """Execute the Quick Audit process."""
    netaudit_bp = current_app.blueprints.get("netaudit")
    data = request.get_json()

    device_list = data.get("devices", [])
    check_list = data.get("checks", [])
    connector = data.get("connector", {})

    session["creds"] = {
        "jumphost_ip": connector.get("jumphost_ip"),
        "jumphost_username": connector.get("jumphost_username"),
        "jumphost_password": connector.get("jumphost_password"),
        "network_username": connector.get("network_username"),
        "network_password": connector.get("network_password"),
    }

    devices = [
        {
            "device": device,
            "check_list": check_list,
            "connector": connector,
        }
        for device in device_list
    ]

    context = {}

    audit_service = netaudit_bp.services.AuditService(
        devices,
        netaudit_bp.CHECKS_DIR,
        netaudit_bp.FACTS_DIR,
        context=context,
    )

    try:
        audit_service.start_thread_executor()
        audit_service.wait_for_completion()
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500

    report_id = (
        f"QuickAudit_{datetime.now().strftime('%Y-%m-%d_%H.%M')}.json"
    )
    report_path = os.path.join(
        session["userdata"].get("reports_dir"), report_id
    )

    try:
        with open(report_path, "w", encoding="utf-8") as file:
            json.dump(audit_service.results, file, indent=4)
    except Exception:
        return jsonify({"success": False, "message": "Report save failed"}), 500

    session["last_report_path"] = report_path

    return jsonify(
        {
            "success": True,
            "message": "QuickAudit run completed",
        }
    ), 200


def quickaudit_report():
    """Retrieve the latest audit report."""
    last_report_path = session.get("last_report_path")

    if not last_report_path:
        return jsonify({"error": "No report found"}), 404

    try:
        with open(last_report_path, "r", encoding="utf-8") as file:
            results = json.load(file)
    except Exception:
        return jsonify({"error": "Failed to read report"}), 500

    return jsonify(results)


def export_report():
    """Export audit results to an Excel file."""
    netaudit_bp = current_app.blueprints.get("netaudit")
    payload = request.get_json()

    if not payload or "data" not in payload:
        return jsonify({"error": "Missing data"}), 400

    data = payload["data"]
    if not data:
        return jsonify({"error": "No data to export"}), 400

    status_codes = netaudit_bp.constants.AUDIT_STATUS_CODES

    timestamp = datetime.now().strftime("%Y-%m-%d_%H.%M")
    filename = f"QuickAudit_{timestamp}.xlsx"

    report_dir = session["userdata"].get("reports_dir")
    os.makedirs(report_dir, exist_ok=True)
    filepath = os.path.join(report_dir, filename)

    try:
        wb = XLBW(filepath)
        ws = wb.add_worksheet()

        status_formats = {
            code: wb.add_format(
                {
                    "bg_color": info["excel_color"],
                    "font_size": "10",
                    "font_name": "Segoe UI",
                    "font_color": "#000000",
                    "valign": "top",
                    "text_wrap": True,
                }
            )
            for code, info in status_codes.items()
        }

        headers = ["Device", "Login", "Overall"]
        first_result = next(iter(data.values()), None)
        if first_result:
            headers.extend(
                check.get("checkName", check)
                for _, check in first_result.get("checks", {}).items()
            )

        ws.write_row(0, 0, headers, wb.ftheader1)

        row = 1
        for _, result in data.items():
            ws.write(row, 0, result["displayName"], wb.ftbody)

            if result.get("login"):
                ws.write(row, 1, "Success", status_formats.get(1))
            else:
                ws.write(row, 1, "Failed", status_formats.get(2))

            overall_status = result.get("status", 0)
            ws.write(
                row,
                2,
                status_codes[overall_status]["label"].title(),
                status_formats.get(overall_status),
            )

            col = 3
            for _, check_result in result.get("checks", {}).items():
                check_status = check_result.get("status", 0)
                ws.write(
                    row,
                    col,
                    status_codes[check_status]["label"].title(),
                    status_formats.get(check_status),
                )
                col += 1

            row += 1

        wb.close()
    except Exception:
        return jsonify({"error": "Export failed"}), 500

    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename,
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )
