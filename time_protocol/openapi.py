"""
TIME Protocol - OpenAPI/Swagger Documentation
Auto-generated API spec + Swagger UI page.
"""

import json


OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "TIME Protocol API",
        "version": "4.0.0",
        "description": "Post-quantum distributed ledger REST API",
        "contact": {"name": "COFC Technologies LTD"},
    },
    "servers": [{"url": "http://127.0.0.1:8080", "description": "Local node"}],
    "paths": {
        "/api/status": {
            "get": {
                "summary": "Get node status",
                "tags": ["Node"],
                "responses": {
                    "200": {
                        "description": "Node status",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Status"}}},
                    }
                },
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
                "parameters": [
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 10}},
                ],
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
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "miner_address": {"type": "string"},
                                    "workers": {"type": "integer", "default": 1},
                                },
                            }
                        }
                    }
                },
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
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["from", "to", "amount"],
                                "properties": {
                                    "from": {"type": "string", "description": "Private key (hex)"},
                                    "to": {"type": "string"},
                                    "amount": {"type": "number"},
                                },
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Transaction sent"}},
            }
        },
    },
    "components": {
        "schemas": {
            "Status": {
                "type": "object",
                "properties": {
                    "height": {"type": "integer"},
                    "total_blocks": {"type": "integer"},
                    "total_utxos": {"type": "integer"},
                    "current_difficulty": {"type": "integer"},
                    "chain_valid": {"type": "boolean"},
                    "mining": {
                        "type": "object",
                        "properties": {
                            "running": {"type": "boolean"},
                            "blocks_mined": {"type": "integer"},
                        },
                    },
                },
            },
        }
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
        .swagger-ui .info .title { color: #e0e6ed; }
        .swagger-ui { background: #0f172a; }
        .swagger-ui .opblock { background: rgba(45,53,97,0.3); border-color: #2d3561; }
        .swagger-ui .opblock .opblock-summary { border-color: #2d3561; }
        .swagger-ui .opblock .opblock-summary-description { color: #8892b0; }
        .swagger-ui .opblock-tag { color: #4a9eff; border-color: #2d3561; }
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
                presets: [SwaggerUIBundle.presets.apis],
                layout: "BaseLayout"
            });
        };
    </script>
</body>
</html>
"""


def get_openapi_json() -> str:
    """Return OpenAPI spec as JSON string."""
    return json.dumps(OPENAPI_SPEC, indent=2)


def get_swagger_ui_html() -> str:
    """Return Swagger UI HTML page."""
    return SWAGGER_UI_HTML
