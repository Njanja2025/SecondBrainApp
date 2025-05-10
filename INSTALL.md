# SecondBrainApp Installation Guide

Welcome to the official SecondBrainApp 2025 Installer. This guide walks you through installation on **macOS** and **Windows**.

## macOS Installation

### 1. Download the Installer
[Download macOS ZIP](SecondBrainApp_macOS.zip)

### 2. Unzip the File
Double-click to extract the `SecondBrainApp_macOS.zip`.

### 3. Build the .app (First Time Only)
Open **Terminal**, then run:
```bash
cd path/to/SecondBrainApp/launcher
chmod +x build_mac.sh
./build_mac.sh
```

### 4. Launch the App
Navigate to `dist/SecondBrainApp2025.app` and double-click to run.

> Tip: Use Spotlight (Cmd+Space) and search for "SecondBrainApp".

## Windows Installation

### 1. Download the Installer
[Download Windows ZIP](SecondBrainApp_Windows.zip)

### 2. Unzip the File
Right-click and extract the ZIP file.

### 3. Build the .exe (First Time Only)
Open **Command Prompt** and run:
```bat
cd path\to\SecondBrainApp\launcher
build_win.bat
```

### 4. Launch the App
Navigate to `dist\SecondBrainApp2025.exe` and double-click to launch.

## System Requirements

### macOS
- macOS 11.0 or later
- 4GB RAM minimum (8GB recommended)
- 500MB free disk space
- Internet connection for updates

### Windows
- Windows 10 or later
- 4GB RAM minimum (8GB recommended)
- 500MB free disk space
- Internet connection for updates

## Troubleshooting

### Common Issues

1. **App won't launch**
   - Check system requirements
   - Verify file permissions
   - Run as administrator (Windows)

2. **Build fails**
   - Ensure Python 3.8+ is installed
   - Check for required dependencies
   - Verify build script permissions

3. **Update issues**
   - Check internet connection
   - Clear app cache
   - Reinstall if necessary

## Support

- Website: [https://www.njanja.net](https://www.njanja.net)
- Email: support@njanja.net
- Documentation: [https://docs.njanja.net](https://docs.njanja.net)

## License

© 2025 Njanja Empire. All rights reserved.
Built with Phantom AI. 