import datetime
import logging
import os

from flask import current_app, jsonify, request, session
from sqlitedict import SqliteDict

def get_dataset(dataset):
    """ Fetches the specified dataset from the corresponding database. """
    netaudit_bp = current_app.blueprints.get("netaudit")
    db = getattr(netaudit_bp, f"{dataset}_db", None)
    if db is not None:
        if dataset == "connectors":
            connectors = dict(db)
            for key, data in db.items():
                for field in ["jumphost_password", "network_password"]:
                    if field in data:
                        try:
                            decrypted_value = current_app.cipher.decrypt(data[field])
                            connectors[key][field] = decrypted_value
                        except Exception as e:
                            logging.error(f"Error decrypting {field} for connector {key}: {e}")
                            connectors[key][field] = None
            return jsonify(connectors)
        return jsonify(dict(db))
    return jsonify(error="Dataset not found"), 404

def delete_dataset_items(dataset):
    """ Deletes specified items from the dataset and updates related data accordingly. """
    netaudit_bp = current_app.blueprints.get("netaudit")
    payload = request.get_json()
    keys_to_delete = payload.get("keys", [])
    deleted = []

    for key in keys_to_delete:
        if dataset == "checks":
            file_path = os.path.join(netaudit_bp.CHECKS_DIR, key)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted.append(key)
                except Exception as e:
                    return jsonify(error=str(e)), 500

            for view_name in netaudit_bp.views_db.keys():
                view_data = netaudit_bp.views_db[view_name]
                checks_list = view_data.get("checks", [])
                if key in checks_list:
                    checks_list.remove(key)
                    view_data["checks"] = checks_list
                    netaudit_bp.views_db[view_name] = view_data

            netaudit_bp.checks_db.pop(key, None)

        elif dataset == "devices":
            for view_name in netaudit_bp.views_db.keys():
                view_data = netaudit_bp.views_db[view_name]
                devices_list = view_data.get("devices", [])
                if key in devices_list:
                    devices_list.remove(key)
                    view_data["devices"] = devices_list
                    netaudit_bp.views_db[view_name] = view_data

            os.remove(os.path.join(netaudit_bp.RESULTS_DIR, key))

            netaudit_bp.devices_db.pop(key, None)

        elif dataset == "views":
            devices = netaudit_bp.views_db.get(key, {}).get("devices", [])
            netaudit_bp.views_db.pop(key, None)
            update_device_results_upon_view_change(devices)

        elif dataset == "connectors":
            netaudit_bp.connectors_db.pop(key, None)

        deleted.append(key)

    logging.info(f"Deleted items from {dataset}: {deleted}")
    return jsonify(deleted=deleted)

def save_dataset_item(dataset):
    """ Saves or updates an item in the specified dataset and updates related data accordingly. """
    netaudit_bp = current_app.blueprints.get("netaudit")
    payload = request.get_json()
    key = payload.get("key")
    data = payload.get("data", {})

    if dataset == "checks":
        file_path = os.path.join(netaudit_bp.CHECKS_DIR, key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(data)

    elif dataset == "views":
        existing_view = netaudit_bp.views_db.get(key, {})
        data["devices"] = existing_view.get("devices", [])
        netaudit_bp.views_db[key] = data
        update_device_results_upon_view_change(data["devices"])

    elif dataset == "devices":
        view_names = data.get("view", [])
        devices = key.split(",")
        for device in devices:
            device = device.strip()
            for view_name in view_names:
                view = netaudit_bp.views_db.get(view_name, {})
                devices_list = view.get("devices", [])
                if device not in devices_list:
                    devices_list.append(device)
                view["devices"] = devices_list
                netaudit_bp.views_db[view_name] = view

            for other_view_name in netaudit_bp.views_db.keys():
                if other_view_name not in view_names:
                    view_data = netaudit_bp.views_db[other_view_name]
                    devices_list = view_data.get("devices", [])
                    if device in devices_list:
                        devices_list.remove(device)
                        view_data["devices"] = devices_list
                        netaudit_bp.views_db[other_view_name] = view_data

            save_device_results_util(device, {})
            data.update({"date": datetime.datetime.now().isoformat(), "user": session.get("username", "Unknown")})
            netaudit_bp.devices_db.update({device: data})

    elif dataset == "connectors":
        for field in ["jumphost_password", "network_password"]:
            data[field] = current_app.cipher.encrypt(data[field])
        netaudit_bp.connectors_db.update({key: data})

    logging.info(f"Saved/Updated item in {dataset}: {key}")
    return jsonify(success=True, key=key, data=data)

def update_device_results_upon_view_change(view_devices):
    """ Updates device results based on changes to views, ensuring that only relevant checks are retained and statuses are updated accordingly. """
    netaudit_bp = current_app.blueprints.get("netaudit")
    views = netaudit_bp.views_db
    all_checks = set()
    for view in views.values():
        for check in view.get("checks", []):
            all_checks.add(check)
    for device in view_devices:
        device_results = get_device_results(device).get_json()
        status = 1
        if not device_results.get("login"):
            status = 2
        for check in list(device_results.get("checks", {}).keys()):
            check_status = device_results["checks"][check].get("status", 0)
            if check not in all_checks:
                device_results["checks"].pop(check, None)
            elif check_status in [2, 5]:
                status = 2
        device_results["status"] = status
        save_device_results_util(device, device_results, clear_missing=True)

def get_device_results(device_id):
    """ Fetches the results for a specific device from its corresponding database and returns it as JSON. """
    netaudit_bp = current_app.blueprints.get("netaudit")
    db_path = os.path.join(netaudit_bp.RESULTS_DIR, f"{device_id}.sqlite")
    device_db = SqliteDict(db_path, autocommit=True)
    results = dict(device_db)
    device_db.close()

    return jsonify(results)

def save_device_results(device_id):
    """ Saves the results for a specific device by merging incoming data with existing data and updating the corresponding database. """
    data = request.get_json()
    success = save_device_results_util(device_id, data)
    if success:
        return jsonify(success=True, device_id=device_id)
    return jsonify(error="Failed to save device results"), 500

def save_followup():
    """ Saves follow-up actions and comments for a list of devices, updating their results accordingly. """
    data = request.get_json()
    devices_list = data.get("devices", [])
    user_action = data.get("user_action", "").strip()
    user_comments = data.get("user_comments", "").strip()

    if not devices_list:
        return jsonify({"error": "No devices provided"}), 400

    updated_devices = []
    for device_id in devices_list:
        update_data = {
            "user_action": user_action,
            "user_comments": user_comments
        }
        success = save_device_results_util(device_id, update_data)
        if success:
            updated_devices.append(device_id)

    logging.info(f"Follow-up saved for devices: {updated_devices}")
    return jsonify({"success": True, "updated_devices": updated_devices})

def save_device_results_util(device_id, data, clear_missing=False):
    """ Internal function to save device results by merging incoming data with existing data and updating the corresponding database. """
    netaudit_bp = current_app.blueprints.get("netaudit")
    db_path = os.path.join(netaudit_bp.RESULTS_DIR, f"{device_id}.sqlite")
    device_db = SqliteDict(db_path, autocommit=True)

    if not dict(device_db):
        device_db.update({
            "last_audit": "0001-01-01T00:00.000000",
            "login": None,
            "hostname": device_id,
            "raw": {},
            "facts": {},
            "checks": {},
            "status": 0,
            "user_action": "",
            "user_comments": ""
        })

    if clear_missing:
        merged_data = data.copy()

    else:
        existing_data = dict(device_db)
        merged_data = existing_data.copy()

        for k, v in data.items():
            if isinstance(v, dict) and isinstance(merged_data.get(k), dict):
                merged_data[k].update(v)
            else:
                merged_data[k] = v

    device_db.update(merged_data)
    logging.info(f"Device results saved for {device_id}")
    device_db.close()
    return True