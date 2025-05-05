"""
SecondBrain App packaging configuration.
"""
from setuptools import setup

APP = ['src/main.py']
DATA_FILES = [
    ('phantom_logs', []),  # Empty directory for logs
    ('config', ['src/secondbrain/config/config.json']),  # Config files
]
OPTIONS = {
    'argv_emulation': True,
    'includes': [
        'whisper',
        'web3',
        'gtts',
        'cryptography',
        'eth_account',
        'eth_utils',
    ],
    'packages': [
        'secondbrain',
        'requests',
        'asyncio',
        'logging',
        'dotenv',
        'base64',
        'hashlib',
    ],
    'iconfile': 'assets/brain_mic_icon.icns',  # Will add this later
    'plist': {
        'CFBundleName': 'SecondBrain',
        'CFBundleDisplayName': 'SecondBrain AI',
        'CFBundleIdentifier': 'com.njanja.secondbrain',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSMinimumSystemVersion': '10.12',
        'NSHumanReadableCopyright': 'Copyright © 2024 Njanja Technologies',
        'NSHighResolutionCapable': True,
    }
} 