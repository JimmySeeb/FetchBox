"""Production WSGI entry point.

Authentication is enabled when both FETCHBOX_USERNAME and FETCHBOX_PASSWORD are set.
"""
from app import app
