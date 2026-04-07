import os

from flask import Blueprint
from sqlitedict import SqliteDict

from . import constants, checkprompt, routes, services

class NetAudit(Blueprint):
    meta = {
        "name": "NetAudit",
        "description": "Network Auditing and Compliance",
        "version": "1.0.0",
        "icon": "netaudit.ico",
        "url_prefix": "/netaudit"
    }


    def __init__(self, **kwargs):
        super().__init__(
            "netaudit",
            __name__,
            url_prefix="/netaudit",
            template_folder="templates",
            static_folder="static",
            **kwargs
        )
        self.constants = constants
        self.checkprompt = checkprompt
        self.routes = routes
        self.services = services
        self.setup_paths()
        self.setup_directories()
        self.setup_db()
        self.setup_directories()
        self.setup_routes()

    def setup_paths(self):
        """ Sets up the directory paths for the NetAudit blueprint, allowing for customization through keyword arguments or defaulting to a standard structure within the user's home directory. """
        self.HOME_DIR = os.path.join(os.path.expanduser("~"), ".netaudit")
        self.CHECKS_DIR = os.path.join(self.HOME_DIR, "checks")
        self.FACTS_DIR = os.path.join(self.HOME_DIR, "facts")
        self.RESULTS_DIR = os.path.join(self.HOME_DIR, "results")
        self.DB_DIR = os.path.join(self.HOME_DIR, "db")

    def setup_directories(self):
        """ Ensures that all necessary directories for the NetAudit blueprint exist, creating them if they do not. """
        for d in [
            self.HOME_DIR,
            self.CHECKS_DIR,
            self.FACTS_DIR,
            self.RESULTS_DIR,
            self.DB_DIR
        ]:
            os.makedirs(d, exist_ok=True)

    def setup_db(self):
        """ Initializes the databases for views, devices, checks, facts, and results using SqliteDict, storing them in the designated database directory for the NetAudit blueprint. """
        self.views_db = SqliteDict(os.path.join(self.DB_DIR, "views"), autocommit=True)
        self.devices_db = SqliteDict(os.path.join(self.DB_DIR, "devices"), autocommit=True)
        self.checks_db = SqliteDict(os.path.join(self.DB_DIR, "checks"), autocommit=True)
        self.facts_db = SqliteDict(os.path.join(self.DB_DIR, "facts"), autocommit=True)
        self.connectors_db = SqliteDict(os.path.join(self.DB_DIR, "connections"), autocommit=True)

    def setup_routes(self):
        """ Registers the routes defined in the NetAudit blueprint's routes module, allowing the blueprint to handle incoming requests according to the specified endpoints and methods. """
        for route in self.routes.routes:
            self.add_url_rule(**route)