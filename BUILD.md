# Building SecondBrain for macOS

This document describes how to build the SecondBrain application for macOS.

## Prerequisites

Before building, ensure you have the following installed:

1. Python 3.7 or later
2. pip (Python package manager)
3. ImageMagick (for icon generation)
4. create-dmg (for creating DMG files)
5. Required Python packages:
   - schedule
   - dropbox
   - google-api-python-client
   - google-auth-httplib2
   - google-auth-oauthlib

You can install the required Python packages using:

```bash
pip3 install -r requirements.txt
```

## Build Process

The build process is automated using three scripts:

1. `build_macos.sh`: Creates the .app bundle structure
2. `build_icon.sh`: Generates the application icon
3. `build_all.sh`: Orchestrates the entire build process

### Quick Build

To build the application with a single command:

```bash
./build_all.sh
```

This will:
1. Check dependencies
2. Clean the build directory
3. Run tests
4. Build the application
5. Generate the icon
6. Create distribution files

### Manual Build

If you prefer to build step by step:

1. Create the .app bundle:
   ```bash
   ./build_macos.sh
   ```

2. Generate the application icon:
   ```bash
   ./build_icon.sh
   ```

3. Create distribution files:
   ```bash
   cd build
   create-dmg --volname "SecondBrain" --volicon "SecondBrain.app/Contents/Resources/AppIcon.icns" --window-pos 200 120 --window-size 800 400 --icon-size 100 --icon "SecondBrain.app" 200 190 --hide-extension "SecondBrain.app" --app-drop-link 600 185 "SecondBrain-1.0.0.dmg" "SecondBrain.app"
   ```

## Build Output

The build process creates the following files in the `build/dist` directory:

- `SecondBrain.app`: The application bundle
- `SecondBrain-1.0.0.dmg`: Disk image for distribution
- `SecondBrain-1.0.0.zip`: Compressed archive

## Application Structure

The built application has the following structure:

```
SecondBrain.app/
├── Contents/
│   ├── Info.plist
│   ├── MacOS/
│   │   ├── secondbrain
│   │   ├── src/
│   │   ├── tests/
│   │   ├── docs/
│   │   ├── requirements.txt
│   │   └── setup.sh
│   ├── Resources/
│   │   └── AppIcon.icns
│   └── Frameworks/
└── README.txt
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   - Ensure all required tools are installed
   - Check Python package installation

2. **Icon Generation Fails**
   - Verify ImageMagick installation
   - Check SVG file format

3. **DMG Creation Fails**
   - Install create-dmg: `brew install create-dmg`
   - Check disk space

4. **Python Package Issues**
   - Update pip: `pip3 install --upgrade pip`
   - Install packages: `pip3 install -r requirements.txt`

### Build Logs

Build logs are written to the console. For more detailed logging, you can redirect the output:

```bash
./build_all.sh > build.log 2>&1
```

## Distribution

The built application can be distributed in two formats:

1. **DMG File**
   - Professional distribution format
   - Includes application icon and background
   - Easy installation for users

2. **ZIP Archive**
   - Alternative distribution format
   - Smaller file size
   - Manual installation required

## Code Signing

For production distribution, the application should be code signed:

1. Obtain an Apple Developer ID
2. Sign the application:
   ```bash
   codesign --force --deep --sign "Developer ID Application: Your Name (TEAM_ID)" "build/dist/SecondBrain.app"
   ```
3. Notarize the application:
   ```bash
   xcrun notarytool submit "build/dist/SecondBrain.app" --apple-id "your@email.com" --password "app-specific-password" --team-id "TEAM_ID"
   ```

## Version Control

The build scripts use the version number defined in `build_all.sh`. To update the version:

1. Update the `VERSION` variable in `build_all.sh`
2. Update version numbers in other relevant files
3. Rebuild the application

## Contributing

When contributing to the build process:

1. Follow the existing script structure
2. Add appropriate error handling
3. Update this documentation
4. Test the build process thoroughly 