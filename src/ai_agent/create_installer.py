import os
import sys
import shutil
from pathlib import Path
import subprocess
import plistlib

def create_installer():
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    app_name = "BaddyAgent.app"
    app_path = base_dir / app_name
    installer_path = base_dir / "BaddyAgent.pkg"
    
    # Create distribution XML
    distribution_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>Baddy Agent</title>
    <organization>com.njanja</organization>
    <domains enable_localSystem="true"/>
    <options customize="never" require-scripts="true"/>
    <volume-check>
        <allowed-os-versions>
            <os-version min="10.13"/>
        </allowed-os-versions>
    </volume-check>
    <choices-outline>
        <line choice="com.njanja.baddyagent"/>
    </choices-outline>
    <choice id="com.njanja.baddyagent" title="Baddy Agent">
        <pkg-ref id="com.njanja.baddyagent"/>
    </choice>
    <pkg-ref id="com.njanja.baddyagent" auth="Root">BaddyAgent.pkg</pkg-ref>
</installer-gui-script>
"""
    
    # Create component property list
    component_plist = {
        "CFBundleIdentifier": "com.njanja.baddyagent",
        "CFBundleName": "BaddyAgent",
        "CFBundleShortVersionString": "1.0",
        "IFMajorVersion": 1,
        "IFMinorVersion": 0,
        "IFPkgFlagAllowBackRev": False,
        "IFPkgFlagAuthorizationAction": "RootAuthorization",
        "IFPkgFlagDefaultLocation": "/Applications",
        "IFPkgFlagInstallFat": False,
        "IFPkgFlagIsRequired": True,
        "IFPkgFlagRelocatable": False,
        "IFPkgFlagRestartAction": "NoRestart",
        "IFPkgFlagRootVolumeOnly": False,
        "IFPkgFlagUpdateInstalledLanguages": False,
        "IFPkgFormatVersion": "0.100",
    }
    
    # Create temporary directory for package creation
    temp_dir = base_dir / "temp_pkg"
    temp_dir.mkdir(exist_ok=True)
    
    # Write distribution XML
    with open(temp_dir / "distribution.xml", "w") as f:
        f.write(distribution_xml)
    
    # Write component property list
    with open(temp_dir / "component.plist", "wb") as f:
        plistlib.dump(component_plist, f)
    
    # Create the package
    subprocess.run([
        "pkgbuild",
        "--root", str(app_path),
        "--install-location", "/Applications",
        "--component-plist", str(temp_dir / "component.plist"),
        str(temp_dir / "BaddyAgent.pkg")
    ])
    
    # Create the installer
    subprocess.run([
        "productbuild",
        "--distribution", str(temp_dir / "distribution.xml"),
        "--package-path", str(temp_dir),
        str(installer_path)
    ])
    
    # Clean up
    shutil.rmtree(temp_dir)
    
    print(f"Installer created at: {installer_path}")
    return installer_path

if __name__ == "__main__":
    create_installer() 