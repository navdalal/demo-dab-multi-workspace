"""Shared helpers used by all bundle notebooks.

Bundles sync this directory into the workspace via `sync.paths`,
so notebooks add the workspace path to sys.path and import from here.
"""

from datetime import datetime, timezone


SHARED_VERSION = "1.0.0"


def greet(workspace_label: str) -> str:
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return (
        f"[shared_utils v{SHARED_VERSION}] hello from workspace "
        f"'{workspace_label}' at {ts} UTC"
    )


def fqn(catalog: str, schema: str, table: str) -> str:
    return f"{catalog}.{schema}.{table}"
