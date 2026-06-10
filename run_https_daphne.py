# run_https_daphne.py
import os
import subprocess
from pathlib import Path

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pms.settings")

# Initialize Django
import django
django.setup()

if __name__ == "__main__":
    project_root = Path(__file__).parent
    
    # Run Daphne with HTTPS using subprocess (correct syntax)
    cmd = [
        "daphne",
        "-b", "127.0.0.1",
        "-p", "8000",
        "-e", f"ssl:8000:privateKey={project_root / 'certs' / 'localhost+2-key.pem'}:certKey={project_root / 'certs' / 'localhost+2.pem'}",
        "pms.asgi:application"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd)