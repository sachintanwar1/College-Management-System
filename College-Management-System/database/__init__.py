# database/__init__.py

"""
Database package initializer for Advanced Face Attendance System.
This file allows `from database import db` or `from database.models import Student` etc.
"""

from .models import db, create_all_if_needed

__all__ = [
    "db",
    "create_all_if_needed",
]
