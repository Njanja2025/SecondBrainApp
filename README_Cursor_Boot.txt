SecondBrain App - Cursor Launch System
====================================

This is a code-level launch system for the SecondBrain application, designed to work seamlessly with Cursor IDE.

Quick Start
----------
1. Open Cursor IDE
2. Clone the repository:
   ```bash
   git clone https://github.com/SecondBrainApp-2025/LaunchCode.git
   cd LaunchCode
   ```
3. Run the setup script:
   ```bash
   bash setup.sh
   ```
4. Launch the app:
   ```bash
   python3 launch_secondbrain.py
   ```

Alternative Launch Methods
------------------------
1. Double-click `launch.command` (macOS only)
2. Use Cursor's built-in run functionality:
   - Open `launch_secondbrain.py`
   - Click the "Run" button or press Cmd/Ctrl + R

Project Structure
---------------
- `launch_secondbrain.py` - Main entry point
- `app_core/` - Core application modules:
  - `njax.py` - Main processing engine
  - `vault.py` - Secure storage system
  - `voice.py` - Voice interaction
  - `forge.py` - Plugin system
- `requirements.txt` - Python dependencies
- `launch.command` - macOS launcher script

Development Setup
---------------
1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install development tools:
   ```bash
   pip install -r requirements-dev.txt
   ```

Running Tests
-----------
```bash
pytest tests/
```

Code Style
---------
- Format code: `black .`
- Lint code: `flake8`
- Type checking: `mypy .`

Troubleshooting
-------------
1. If you get "Python not found":
   - Install Python 3.8 or later
   - Ensure Python is in your PATH

2. If dependencies fail to install:
   - Update pip: `python3 -m pip install --upgrade pip`
   - Try installing requirements one by one

3. If the app fails to launch:
   - Check launch.log for errors
   - Ensure all dependencies are installed
   - Verify Python version compatibility

Support
-------
For issues and feature requests:
1. Check the GitHub repository
2. Open an issue with detailed information
3. Include logs and error messages

License
-------
This project is licensed under the MIT License - see LICENSE file for details. 