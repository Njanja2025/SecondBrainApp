"""
Setup configuration for SecondBrain
"""

import os
import shutil
import sys
from setuptools import setup, find_packages

# Ensure required directories exist
required_dirs = ["config", "gui", "payments", "utils", "logs", "src"]
for dir_name in required_dirs:
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

# Clean previous builds
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")

# Run PyInstaller if --build-app flag is provided
if "--build-app" in sys.argv:
    import PyInstaller.__main__

    # Remove the flag from sys.argv
    sys.argv.remove("--build-app")

    # Run PyInstaller
    PyInstaller.__main__.run(
        [
            "main.py",
            "--name=SecondBrainApp2025",
            "--windowed",
            "--clean",
            "--add-data=config:config",
            "--add-data=gui:gui",
            "--add-data=payments:payments",
            "--add-data=utils:utils",
            "--add-data=logs:logs",
            "--add-data=src:src",
            "--add-data=requirements.txt:.",
            "--add-data=README.md:.",
            "--icon=assets/secondbrain.icns",
        ]
    )

    # Create delivery package
    def create_delivery_package():
        # Create delivery directory
        delivery_dir = "delivery_package"
        if not os.path.exists(delivery_dir):
            os.makedirs(delivery_dir)

        # Copy app to delivery directory
        app_name = "SecondBrainApp2025.app"
        if os.path.exists(f"dist/{app_name}"):
            shutil.copytree(f"dist/{app_name}", f"{delivery_dir}/{app_name}")

        # Copy additional files
        shutil.copy("README.md", delivery_dir)
        shutil.copy("requirements.txt", delivery_dir)

        # Create zip file
        shutil.make_archive("SecondBrainApp_Package", "zip", delivery_dir)

        print("Delivery package created successfully!")

    # Create delivery package after build
    create_delivery_package()

# Regular setup configuration
setup(
    name="secondbrain",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=["boto3", "dropbox", "pyicloud", "schedule", "python-dotenv"],
    python_requires=">=3.7",
    author="SecondBrain Team",
    author_email="support@secondbrain.ai",
    description="SecondBrain Companion Journaling Backup System",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/secondbrain",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
