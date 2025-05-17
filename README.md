# Baddy Agent v1.0 - Launch-Ready Edition

A powerful AI assistant with voice control, system monitoring, and cloud integration capabilities.

## Features

- 🎤 Voice Command Interface
- 🤖 Smart Tray Integration
- 🔍 System Monitoring
- ☁️ Cloud Sync (Google Drive, Dropbox)
- 🛡️ Phantom Mode
- 📊 Web Dashboard
- 🔄 Auto-Update System

## Installation

### Quick Install

1. Download the latest release from the [Releases](https://github.com/Njanja2025/SecondBrainApp/releases) page
2. Run the installation script:
```bash
./install_baddy_agent.command
```

### Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/Njanja2025/SecondBrainApp.git
cd SecondBrainApp
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the installation script:
```bash
./install_baddy_agent.command
```

## Usage

### Starting Baddy Agent

1. **Quick Launch**: Double-click `BaddyAgent.app` in Applications
2. **Command Line**: Run `./Launch_BaddyAgent.command`
3. **Tray Icon**: Click the 🤖 icon in the menu bar

### Voice Commands

- "Hey Baddy" - Activate voice recognition
- "Start Phantom Mode" - Enable enhanced security
- "Show Status" - Display system information
- "Open Dashboard" - Launch web interface
- "Sync Now" - Trigger cloud synchronization

### Tray Menu Features

- Start/Stop Voice
- Activate/Deactivate Phantom Mode
- System Status
- Quick Access to:
  - Logs
  - Diagnostics
  - Dashboard
  - GitHub Repository
  - Web Console
- Actions:
  - Sync Now
  - Recovery Mode
  - Shutdown

## Configuration

Edit `src/ai_agent/config.yaml` to customize:
- Cloud service settings
- System monitoring thresholds
- Notification preferences
- Log retention policies

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Building from Source

1. Create app bundle:
```bash
./create_app_bundle.command
```

2. Create DMG installer:
```bash
./create_dmg.command
```

## Support

- GitHub Issues: [Report Bugs](https://github.com/Njanja2025/SecondBrainApp/issues)
- Documentation: [Wiki](https://github.com/Njanja2025/SecondBrainApp/wiki)
- Email: support@njanja.net

## License

© 2024 Njanja2025. All rights reserved.

## Acknowledgments

- OpenAI for voice recognition
- Google Cloud for storage integration
- Dropbox for file synchronization
- The open-source community for various tools and libraries 