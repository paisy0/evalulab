import sys
from dotenv import load_dotenv
import os

load_dotenv()

print(f"Python : {sys.version.split()[0]}")

installed = []
missing = []

for pkg in ["ragas", "deepeval", "apisağlayıcısı", "pandas"]:
    try:
        __import__(pkg)
        installed.append(pkg)
    except ImportError:
        missing.append(pkg)

if installed:
    print(f"Installed : {', '.join(installed)}")
if missing:
    print(f"Missing   : {', '.join(missing)}")

key = os.getenv("blabla_API_KEY")
print(f"API Key   : {'found' if key else 'NOT FOUND'}")
