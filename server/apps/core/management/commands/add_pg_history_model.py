"""
Django expects management commands to live in `management/commands/<name>.py`.

The actual implementation is in `server.apps.core.management.add_pg_history_model`
to keep backward compatibility with direct imports.
"""

from server.apps.core.management.add_pg_history_model import Command  # noqa: F401

