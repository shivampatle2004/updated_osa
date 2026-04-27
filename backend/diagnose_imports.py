import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

print(f"Checking imports in {backend_dir}...")

try:
    import main
    print("✓ Successfully imported main.py")
except Exception as e:
    print(f"✗ Error importing main.py: {e}")
    import traceback
    traceback.print_exc()

modules_to_check = [
    "models",
    "schemas",
    "database",
    "routers.files",
    "routers.graphs",
    "routers.smart",
    "routers.sql",
    "routers.etl",
    "services.data_processor",
    "services.graph_engine",
    "services.etl_scheduler"
]

for mod in modules_to_check:
    try:
        __import__(mod)
        print(f"✓ Successfully imported {mod}")
    except Exception as e:
        print(f"✗ Error importing {mod}: {e}")
        import traceback
        traceback.print_exc()
