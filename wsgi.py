"""Production WSGI entry point; refuse to serve publicly without authentication."""
import os

if not os.environ.get("FETCHBOX_USERNAME") or not os.environ.get("FETCHBOX_PASSWORD"):
    raise RuntimeError(
        "Set FETCHBOX_USERNAME and FETCHBOX_PASSWORD before starting the web service."
    )

from app import app
