"""
NetAudit Flask Blueprint module.

Provides the NetAudit blueprint, responsible for initializing
directories, database connections, and routes for network auditing
and compliance functionality.

File path: blueprint.py
"""

import logging
import os

from flask import Blueprint
from sqlitedict import SqliteDict

from . import checkprompt, constants, routes, services

logger = logging.getLogger(__name__)


class NetAudit(Blueprint):
    """Custom Flask Blueprint for NetAudit functionality."""

    meta = {
        "name": "NetAudit",
        "description": "Network Auditing and Compliance",
        "version": "1.0.0",
        "icon": "netaudit.ico",
        "url_prefix": "/netaudit",
    }

    def __init__(self, **kwargs):
        """Initialize the NetAudit blueprint."""

        super().__init__(
            "netaudit",
            __name__,
            url_prefix="/netaudit",
            template_folder="templates",
            static_folder="static",
            **kwargs,
        )

        self.constants = constants
        self.checkprompt = checkprompt
        self.routes = routes
        self.services = services

        self.setup_paths()
        self.setup_directories()
        self.setup_db()
        self.setup_routes()

    def setup_paths(self):
        """Set up directory paths for NetAudit."""
        self.HOME_DIR = os.path.join(
            os.path.expanduser("~"), ".netaudit"
        )
        self.CHECKS_DIR = os.path.join(self.HOME_DIR, "checks")
        self.FACTS_DIR = os.path.join(self.HOME_DIR, "facts")
        self.RESULTS_DIR = os.path.join(self.HOME_DIR, "results")
        self.DB_DIR = os.path.join(self.HOME_DIR, "db")

    def setup_directories(self):
        """Ensure required directories exist."""
        directories = [
            self.HOME_DIR,
            self.CHECKS_DIR,
            self.FACTS_DIR,
            self.RESULTS_DIR,
            self.DB_DIR,
        ]

        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
            except OSError:
                logger.exception(
                    "Failed to create directory: %s", directory
                )
                raise

    def setup_db(self):
        """Initialize SQLite-backed dictionaries."""
        try:
            self.views_db = SqliteDict(
                os.path.join(self.DB_DIR, "views.sqlite"),
                autocommit=True,
            )
            self.devices_db = SqliteDict(
                os.path.join(self.DB_DIR, "devices.sqlite"),
                autocommit=True,
            )
            self.checks_db = SqliteDict(
                os.path.join(self.DB_DIR, "checks.sqlite"),
                autocommit=True,
            )
            self.facts_db = SqliteDict(
                os.path.join(self.DB_DIR, "facts.sqlite"),
                autocommit=True,
            )
            self.connectors_db = SqliteDict(
                os.path.join(self.DB_DIR, "connections.sqlite"),
                autocommit=True,
            )

        except Exception:
            raise

    def setup_routes(self):
        """Register blueprint routes."""
        for route in self.routes.routes:
            try:
                self.add_url_rule(**route)
            except Exception:
                logger.exception(
                    "Failed to register route: %s", route
                )
                raise
