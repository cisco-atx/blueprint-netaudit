"""
Blueprint initialization for NetAudit module.

This module exposes the NetAudit blueprint class for use in the
application. It serves as a simple entry point for importing the
blueprint.

File path: routes/__init__.py
"""

# Local application imports
from .blueprint import NetAudit

# Blueprint class reference
BP_CLASS = NetAudit
