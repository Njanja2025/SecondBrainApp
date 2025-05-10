# SecondBrain

A powerful personal knowledge management system built with Python.

## Features

- Advanced video rendering with effects
- Financial report generation
- Hotkey management
- GUI interface
- Cloud backup integration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/secondbrain/app.git
cd secondbrain
```

2. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

## Usage

### Video Rendering

```python
from src.secondbrain.marketing import render_video

# Render with default settings
render_video()

# Render with custom preset
render_video(preset="premium")
```

### Financial Reports

```python
from src.secondbrain.finance import generate_income_report, ReportType

# Generate income report
generate_income_report(
    report_type=ReportType.INCOME,
    output_path="reports/income.pdf"
)
```

### Hotkeys

```python
from src.secondbrain.utils import Hotkey

hotkey = Hotkey()
hotkey.register("ctrl+shift+s", save_callback)
```

## Development

1. Set up environment variables:
```bash
export PYTHONPATH=.
export SECONDBRAIN_BASE_DIR=~/secondbrain
export ENABLE_ALERTS=true
export ENABLE_EMAIL_ALERTS=true
export ENABLE_HEALTH_CHECKS=true
export LOG_LEVEL=DEBUG
```

2. Run tests:
```bash
python -m pytest tests/
```

## License

MIT License - see LICENSE file for details 