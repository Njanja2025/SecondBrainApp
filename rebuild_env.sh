#!/bin/bash

echo ">> Removing old venv..."
rm -rf venv

echo ">> Creating new venv with Python 3.11..."
/opt/homebrew/opt/python@3.11/bin/python3 -m venv venv

echo ">> Activating virtual environment..."
source venv/bin/activate

echo ">> Upgrading pip, setuptools, wheel..."
pip install --upgrade pip setuptools wheel

echo ">> Installing PyTorch for Apple Silicon..."
pip install torch torchvision torchaudio

echo ">> Installing all other dependencies..."
pip install -r requirements.txt

echo ">> Running voice output system..."
python voice_output.py 