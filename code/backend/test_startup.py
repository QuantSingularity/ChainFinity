#!/usr/bin/env python3
"""
Simple startup test without database connections
Tests if the application can at least be created and configured
"""

import sys

sys.path.insert(0, ".")

try:
    from app.main import app

    print(" App imported successfully")

    # Check routes
    routes_count = len(app.routes)
    print(f" Registered {routes_count} routes")

    # List main route prefixes
    prefixes = set()
    for route in app.routes:
        if hasattr(route, "path"):
            path_parts = route.path.split("/")
            if len(path_parts) > 1 and path_parts[1]:
                prefixes.add(f"/{path_parts[1]}")

    print(f" Route prefixes: {', '.join(sorted(prefixes))}")

    print("\n Application structure is valid!")
    print(
        " - To run with database: Ensure PostgreSQL is running and run 'uvicorn app.main:app --reload'"
    )
    print(" - API documentation will be available at: http://localhost:8000/docs")

except Exception as e:
    print(f" Error during app startup: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
