#!/usr/bin/env python3
"""
Simple script to create the final SecondBrainApp bundle
"""

import os
import sys
import zipfile
from pathlib import Path
from datetime import datetime

def create_bundle():
    # Define paths
    root_dir = Path("SecondBrainApp")
    dist_dir = Path("dist")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bundle_name = f"SecondBrainApp_Final_Launch_Bundle_{timestamp}"
    bundle_path = dist_dir / f"{bundle_name}.zip"

    # Create dist directory
    dist_dir.mkdir(exist_ok=True)

    # Create zip file
    with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add project files
        for root, dirs, files in os.walk(root_dir):
            # Skip unnecessary directories
            if any(skip in root for skip in ['.git', '__pycache__']):
                continue
            
            for file in files:
                # Skip unnecessary files
                if file.endswith(('.pyc', '.pyo')):
                    continue
                
                file_path = Path(root) / file
                arcname = file_path.relative_to(root_dir)
                zipf.write(file_path, arcname)
                print(f"Added: {arcname}")

        # Add README.md
        readme_content = """# SecondBrainApp Final Launch Bundle

## Overview
This bundle contains the complete SecondBrainApp system with all modules, including:
- Core Application
- Phantom AI System
- Notification System
- Resource Monitoring
- Crash Tracking
- Daily Summary Reports

## Installation
1. Extract the bundle
2. Install dependencies: `pip install -r requirements.txt`
3. Configure settings in `config/` directory
4. Run the application: `python launcher/main.py`

## Configuration
- Email settings: `config/email_config.json`
- Webhook settings: `config/webhook_config.json`
- Phantom AI settings: `phantom/config/phantom_config.json`

## Features
- Real-time system monitoring
- Automated decision making
- Crash recovery
- Email and webhook notifications
- Daily summary reports
- Resource usage tracking

## Support
For support, please contact: support@secondbrainapp.com
"""
        zipf.writestr('README.md', readme_content)
        print("Added: README.md")

        # Add requirements.txt
        requirements = """psutil>=5.9.0
numpy>=1.21.0
schedule>=1.1.0
requests>=2.26.0
python-dotenv>=0.19.0
"""
        zipf.writestr('requirements.txt', requirements)
        print("Added: requirements.txt")

    print(f"\nBundle created successfully at: {bundle_path}")
    return str(bundle_path)

if __name__ == "__main__":
    try:
        bundle_path = create_bundle()
        print("\nBundle contents:")
        print("- Complete SecondBrainApp system")
        print("- Phantom AI integration")
        print("- Notification system")
        print("- Resource monitoring")
        print("- Crash tracking")
        print("- Daily summary reports")
    except Exception as e:
        print(f"Error creating bundle: {str(e)}")
        sys.exit(1) 