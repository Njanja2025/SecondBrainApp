#!/bin/bash
echo "=== Backing up requirements.txt ==="
cp requirements.txt requirements.txt.bak

echo "=== Updating requirements.txt: replacing pydantic with compatible version ==="
sed -i '' '/pydantic==2.5.2/d' requirements.txt
echo "pydantic==1.10.12" >> requirements.txt

echo "=== Cleaning typing-extensions and upgrading pip tools ==="
pip uninstall typing-extensions -y
pip install --upgrade pip setuptools wheel

echo "=== Installing requirements ==="
pip install -r requirements.txt

echo "=== Checking for dependency conflicts ==="
pip check

echo "=== Environment fix complete ==="

echo "Installing pinned compatible packages..."
pip install -r requirements-compatible.txt

echo "Fixing typing-extensions and dependencies..."
pip install 'typing-extensions==4.5.0' 'pytest-asyncio==0.23.2' 'web3==6.11.3' --force-reinstall

echo "Cleaning up..."
pip check
echo "Environment fixed."
