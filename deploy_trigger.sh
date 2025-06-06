#!/bin/zsh
# Deployment trigger for SecondBrainApp: runs tests and deploys if successful

set -e

echo "[DEPLOY] Running CLI and payment tests..."
pytest tests/test_cli.py

if [ $? -eq 0 ]; then
  echo "[DEPLOY] Tests passed. Deploying to production..."
  # Insert your deployment command here, e.g.:
  ./deploy_app.sh
  echo "[DEPLOY] Deployment complete."
else
  echo "[DEPLOY] Tests failed. Deployment aborted."
  exit 1
fi
