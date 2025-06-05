#!/bin/zsh

# Full update, test, deploy, and tag script for SecondBrainApp
# Exit on error
set -e

# Check for required scripts
for script in ./run_tests.sh ./build_all.sh ./deploy.sh; do
    if [ ! -x "$script" ]; then
        echo "Required script $script not found or not executable. Aborting." >&2
        exit 2
    fi
done

# Check for uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    echo "Warning: You have uncommitted changes. Please commit or stash them before running this script."
    exit 3
fi

# Pull latest changes
echo "Pulling latest changes from git..."
git pull || { echo "Git pull failed. Aborting."; exit 1; }

# Run full test suite
echo "Running full test suite..."
./run_tests.sh || { echo "Tests failed. Aborting deployment."; exit 1; }

echo "Tests passed. Adding and committing changes..."
git add .
COMMIT_MSG="Automated update, test, and deploy on $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$COMMIT_MSG" || echo "Nothing to commit."

echo "Pushing changes to remote..."
git push || { echo "Git push failed. Aborting."; exit 1; }

echo "Building application..."
./build_all.sh || { echo "Build failed. Aborting deployment."; exit 1; }

echo "Deploying application..."
./deploy.sh || { echo "Deploy failed. Aborting."; exit 1; }

# Tag the release with a timestamp
TAG="release-$(date +%Y%m%d%H%M%S)"
git tag -a "$TAG" -m "Automated release on $(date)"
git push origin "$TAG"
echo "Tagged release as $TAG"

echo "Full update, test, deploy, and tag complete."
