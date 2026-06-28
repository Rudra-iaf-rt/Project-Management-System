#!/usr/bin/env python
import os
import sys
import importlib.metadata

_orig_version = importlib.metadata.version
def _mock_version(distribution_name):
    try:
        return _orig_version(distribution_name)
    except OSError:
        if distribution_name == "djangorestframework_simplejwt":
            return "5.3.1"
        return "1.0.0"

importlib.metadata.version = _mock_version

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()