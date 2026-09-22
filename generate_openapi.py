import json
from time_api import app

def export_openapi_spec():
    openapi_schema = app.openapi()
    with open("openapi.json", "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    print("✅ Successfully generated openapi.json for institutional integrations!")

if __name__ == "__main__":
    export_openapi_spec()
