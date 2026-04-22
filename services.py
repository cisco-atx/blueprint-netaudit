"""
Network device auditing service module.

Provides the AuditService class to perform concurrent audits on network
devices using dynamically loaded checks and optional fact gatherers.
Supports threaded execution, connector handling, and structured results.

File path: services.py
"""

import datetime
import importlib.util
import inspect
import logging
import os
import re
import socket
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed

from netcore import GenericHandler

logger = logging.getLogger(__name__)


class AuditService:
    """Service class to perform network device audits."""

    def __init__(self, devices, check_dir, facts_dir=None, context=None):
        """Initialize the AuditService."""
        self.devices = devices
        self.checks_dir = check_dir
        self.context = context
        self.facts_dir = facts_dir
        self.results = {}
        self.connectors = {}
        self.futures = []
        self.gatherers = {}

        if self.facts_dir:
            self.load_facts()

    def get_check_instance(self, check_file, device):
        """Load and return an instance of a check class."""
        file_path = os.path.join(self.checks_dir, check_file)
        module_name = file_path.replace(".py", "")

        spec = importlib.util.spec_from_file_location(
            module_name, file_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return getattr(module, "CHECK_CLASS")(device, self.context)

    def obt_conn(self, device, connector):
        """Establish a network connection to a device."""
        proxy = (
            {
                "hostname": connector["jumphost_ip"],
                "username": connector["jumphost_username"],
                "password": connector["jumphost_password"],
            }
            if connector["jumphost_ip"]
            else None
        )

        try:
            conn = GenericHandler(
                hostname=device,
                username=connector["network_username"],
                password=connector["network_password"],
                proxy=proxy,
                handler="NETMIKO",
                read_timeout_override=1000,
            )
            logger.info("Connected to device '%s' successfully", device)
            return conn
        except Exception as exc:
            logger.error(
                "Connector failed for '%s': %s", device, exc
            )
            return None

    def start_thread_executor(self, max_workers=8):
        """Start thread pool execution for audit tasks."""
        logger.info("Starting audit thread pool execution...")
        executor = ThreadPoolExecutor(max_workers=max_workers)

        for device_data in self.devices:
            future = executor.submit(self.audit_task, device_data)
            self.futures.append(future)

        return self.futures

    def wait_for_completion(self):
        """Wait for all audit tasks to complete."""
        for conn in self.connectors.values():
            if conn:
                conn.disconnect()

        for future in as_completed(self.futures):
            future.result()

        logger.info("All device audits completed.")

    def _get_device_fqdn(self, device, conn):
        """Resolve and return the device FQDN."""
        if re.search(r"^\d{1,3}(\.\d{1,3}){3}$", device):
            try:
                return socket.gethostbyaddr(device)[0]
            except socket.herror:
                if conn:
                    output = conn.sendCommand(
                        "show running-config | include domain"
                    )
                    match = re.search(
                        r"^ip domain[- ]name\s+(\S+)", output, re.M
                    )
                    if match:
                        return f"{conn.base_prompt}.{match.group(1)}"
                    return conn.base_prompt
                return device
        return device

    def audit_task(self, device_data):
        """Perform all checks on a given device."""
        device = device_data.get("device")
        connector = device_data.get("connector")
        check_list = device_data.get("check_list")

        self.results[device] = {
            "last_audit": datetime.datetime.now().isoformat(),
            "login": None,
            "hostname": device,
            "raw": {},
            "facts": {},
            "checks": {
                check_file: {
                    "status": 0,
                    "observation": "",
                    "comments": [],
                }
                for check_file in check_list
            },
        }

        self.connectors[device] = self.obt_conn(device, connector)
        self.results[device]["login"] = bool(
            self.connectors[device]
        )

        if not self.connectors[device]:
            logger.error(
                "Skipping device '%s' due to connector failure", device
            )
            self.results[device]["status"] = 2
            return

        self.results[device]["hostname"] = self._get_device_fqdn(
            device, self.connectors[device]
        )

        if self.gatherers:
            self.results[device]["facts"] = self.gather_facts(
                self.connectors[device]
            )

        for check_file in check_list:
            try:
                check_inst = self.get_check_instance(
                    check_file, device
                )
                last_request = None

                while check_inst.REQUESTS:
                    current_request = (
                        check_inst.REQUESTS.get("device"),
                        check_inst.REQUESTS.get("command"),
                        check_inst.REQUESTS.get("handler"),
                    )

                    if current_request == last_request:
                        break

                    req_device, req_cmd, handler_name = current_request
                    key = f"{req_device}:{req_cmd}"

                    if key not in self.results[device]["raw"]:
                        if not self.connectors.get(req_device):
                            self.connectors[req_device] = self.obt_conn(
                                req_device, connector
                            )

                        if not self.connectors[req_device]:
                            logger.error(
                                "Connector failed for '%s' during "
                                "check '%s' on '%s'",
                                req_device,
                                check_file,
                                device,
                            )
                            break

                        output = self.connectors[
                            req_device
                        ].sendCommand(req_cmd)
                        self.results[device]["raw"][key] = output
                    else:
                        output = self.results[device]["raw"][key]

                    getattr(check_inst, handler_name)(
                        req_device, req_cmd, output
                    )
                    last_request = current_request

                self.results[device]["checks"][
                    check_file
                ] = check_inst.RESULTS

                logger.debug(
                    "Check '%s' completed for '%s'",
                    check_file,
                    device,
                )

            except Exception as exc:
                logger.exception(
                    "Error executing check '%s' on '%s': %s",
                    check_file,
                    device,
                    exc,
                )

        self.results[device]["status"] = 1
        for check_result in self.results[device]["checks"].values():
            if check_result.get("status") in [2, 5]:
                self.results[device]["status"] = 2
                break

        logger.info("Audit task completed for device '%s'", device)

    def load_facts(self):
        """Load fact-gathering functions from directory."""
        for facts_module in os.listdir(self.facts_dir):
            if not facts_module.endswith(".py") or facts_module.startswith(
                    "__"
            ):
                continue

            path = os.path.join(self.facts_dir, facts_module)
            module_name = facts_module.replace(".py", "")

            spec = importlib.util.spec_from_file_location(
                module_name, path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for _, func in inspect.getmembers(
                    module, inspect.isfunction
            ):
                match = re.match(
                    r"^gather_([a-zA-Z0-9_]+)$", func.__name__
                )
                if not match:
                    continue

                name = match.group(1)
                gatherer_id = f"{module_name}.{name}"

                self.gatherers[gatherer_id] = {
                    "name": name,
                    "func": func,
                    "path": path,
                    "description": inspect.getdoc(func)
                                   or "No description.",
                    "code": textwrap.dedent(
                        inspect.getsource(func)
                    ),
                }

    def gather_facts(self, conn):
        """Gather facts using loaded gatherers."""
        facts = {}

        for name, meta in self.gatherers.items():
            func = meta["func"]
            try:
                result = func(conn)
                if isinstance(result, dict):
                    facts.update(result)
            except Exception as exc:
                logger.error(
                    "Error running gatherer '%s': %s", name, exc
                )

        return facts
