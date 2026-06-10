# run_server.py
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pms.settings")
    
    # Add project to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from daphne.cli import CommandLineInterface
    
    print("Starting Daphne Server...")
    CommandLineInterface().run([
        "daphne",
        "-b", "127.0.0.1", 
        "-p", "8000",
        "--verbosity", "3",
        "pms.asgi:application"
    ])