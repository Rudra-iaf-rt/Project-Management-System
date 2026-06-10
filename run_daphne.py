# run_daphne.py
import os
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pms.settings")

# Initialize Django
import django
django.setup()

# Now run Daphne
from daphne.cli import CommandLineInterface

if __name__ == "__main__":
    print("=" * 50)
    print("Starting Daphne Server on http://127.0.0.1:8000")
    print("=" * 50)
    
    CommandLineInterface().run([
        "daphne",
        "-b", "127.0.0.1",
        "-p", "8000",
        "pms.asgi:application"
    ])