#!/usr/bin/env python3
import subprocess
import sys

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"Successfully installed {package}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}: {e}")

def main():
    packages = [
        "psutil",
        "numpy",
        "torch",
        "transformers",
        "scikit-learn",
        "aiohttp",
        "websockets",
        "python-dotenv",
        "pyyaml",
        "loguru",
        "tqdm",
        "SpeechRecognition",
        "gTTS",
        "PyAudio",
        "web3",
        "eth-account",
        "eth-utils",
        "openai-whisper==20230918"
    ]
    
    for package in packages:
        install_package(package)

if __name__ == "__main__":
    main() 