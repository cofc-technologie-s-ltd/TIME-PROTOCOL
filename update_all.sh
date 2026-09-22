#!/bin/bash
# TIME Protocol - Full Update Script
set -e

echo "================================"
echo "  TIME Protocol Update"
echo "================================"
echo ""

# Stage all changes
echo "[1/4] Staging changes..."
git add -A

# Show status
echo ""
echo "[2/4] Git status:"
git status --short

# Commit
echo ""
echo "[3/4] Creating commit..."
git commit -m "docs: professional GitHub presentation

- Modern README with badges, features, and API docs
- Semantic versioning CHANGELOG
- Enhanced .gitignore for Python and TIME Protocol data
- Upgraded CI workflow with Python 3.11/3.12/3.13 matrix
- Docker build verification in CI" || echo "Nothing to commit"

# Push
echo ""
echo "[4/4] Pushing to GitHub..."
git push origin main

echo ""
echo "================================"
echo "  DONE"
echo "================================"
echo ""
echo "Check: https://github.com/cofc-technologie-s-ltd/TIME-PROTOCOL"
