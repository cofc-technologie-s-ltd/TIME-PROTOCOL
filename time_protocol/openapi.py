"""
TIME Protocol - OpenAPI/Swagger Documentation
"""

import json


OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "TIME Protocol API",
        "version": "5.0.0",
        "description": "Post-quantum distributed ledger REST API",
        "contact": {"name": "COFC Technologies LTD"},
    },
    "servers": [{"url": "http://127.0.0.1:8080", "description": "Local node"}],
    "paths": {
        "/api/status": {
            "get": {
                "summary": "Get node status",
                "tags": ["Node"],
                "responses": {"200": {"description": "Node status"}},
            }
        },
        "/api/chain": {
            "get": {
                "summary": "Get full blockchain",
                "tags": ["Blockchain"],
                "responses": {"200": {"description": "Full chain"}},
            }
        },
        "/api/blocks": {
            "get": {
                "summary": "Get recent blocks",
                "tags": ["Blockchain"],
                "responses": {"200": {"description": "Recent blocks"}},
            }
        },
        "/api/block/{index}": {
            "get": {
                "summary": "Get block by index",
                "tags": ["Blockchain"],
                "parameters": [
                    {"name": "index", "in": "path", "required": True, "schema": {"type": "integer"}},
                ],
                "responses": {"200": {"description": "Block data"}},
            }
        },
        "/api/balance/{address}": {
            "get": {
                "summary": "Get address balance",
                "tags": ["Wallet"],
                "parameters": [
                    {"name": "address", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "Balance info"}},
            }
        },
        "/api/difficulty": {
            "get": {
                "summary": "Get difficulty info",
                "tags": ["Mining"],
                "responses": {"200": {"description": "Difficulty stats"}},
            }
        },
        "/api/mining/status": {
            "get": {
                "summary": "Get mining status",
                "tags": ["Mining"],
                "responses": {"200": {"description": "Mining status"}},
            }
        },
        "/api/mining/start": {
            "post": {
                "summary": "Start background mining",
                "tags": ["Mining"],
                "responses": {"200": {"description": "Mining started"}},
            }
        },
        "/api/mining/stop": {
            "post": {
                "summary": "Stop background mining",
                "tags": ["Mining"],
                "responses": {"200": {"description": "Mining stopped"}},
            }
        },
        "/api/mine": {
            "post": {
                "summary": "Mine one block manually",
                "tags": ["Mining"],
                "responses": {"200": {"description": "Block mined"}},
            }
        },
        "/api/tx/send": {
            "post": {
                "summary": "Send transaction",
                "tags": ["Wallet"],
                "responses": {"200": {"description": "Transaction sent"}},
            }
        },
        "/api/metrics": {
            "get": {
                "summary": "Prometheus metrics",
                "tags": ["Monitoring"],
                "responses": {"200": {"description": "Metrics in Prometheus format"}},
            }
        },
    },
}


SWAGGER_UI_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>TIME Protocol API Docs</title>
    <meta charset="utf-8"/>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    <style>
        body { margin: 0; padding: 0; background: #0a0e27; }
        .topbar { background: linear-gradient(135deg, #4a9eff, #7b5cff) !important; }
        .swagger-ui { background: #0f172a; }
        .swagger-ui .info .title { color: #e0e6ed; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {
            SwaggerUIBundle({
                url: "/api/openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
            });
        };
    </script>
</body>
</html>
"""


def get_openapi_json() -> str:
    return json.dumps(OPENAPI_SPEC, indent=2)


def get_swagger_ui_html() -> str:
    return SWAGGER_UI_HTML
