#!/bin/bash

set -e  # Exit on error

echo "Starting deployment..."

echo "Cleaning previous builds..."
rm -rf dist build

echo "Building package..."
python3 setup.py sdist bdist_wheel

echo "Running tests..."
./run_tests.sh

echo "Publishing package to PyPI..."
# Uncomment below line when ready and configure ~/.pypirc or environment variables
# twine upload dist/*

echo "Deployment complete."