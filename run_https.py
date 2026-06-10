# run_https.py
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings module BEFORE importing any Django apps
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pms.settings")

# Now initialize Django
import django
django.setup()

# After Django is ready, import and run Uvicorn
import uvicorn

if __name__ == "__main__":
    # Paths to your certificates
    ssl_keyfile = project_root / "certs" / "localhost+2-key.pem"
    ssl_certfile = project_root / "certs" / "localhost+2.pem"

    # Run server with HTTPS
    uvicorn.run(
        "pms.asgi:application",
        host="127.0.0.1",
        port=8000,
        ssl_keyfile=str(ssl_keyfile),
        ssl_certfile=str(ssl_certfile),
        reload=True,
        log_level="info"
    )