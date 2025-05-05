# SecondBrain Development Guide

## Architecture Overview

### Component Structure
```
SecondBrain
├── GUI (gui.py)
│   ├── User Interface
│   ├── Event Handling
│   └── Theme Management
├── Voice Processor (voice_processor.py)
│   ├── Speech Recognition
│   ├── Audio Capture
│   └── Error Recovery
└── Assistant (assistant.py)
    ├── AI Processing
    ├── Response Generation
    └── State Management
```

### Communication Flow
1. **Voice Input**:
   ```
   Microphone → Voice Processor → Text → Assistant → Response → GUI/Voice Output
   ```

2. **Text Input**:
   ```
   GUI → Assistant → Response → GUI/Voice Output
   ```

## Development Setup

### Prerequisites
- Python 3.8+
- Virtual Environment
- Git
- IDE (VSCode/Cursor recommended)
- macOS for voice features

### Environment Setup
1. **Clone Repository**:
   ```bash
   git clone https://github.com/yourusername/secondbrain.git
   cd secondbrain
   ```

2. **Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Development Dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

### IDE Configuration
1. **VSCode/Cursor Settings**:
   ```json
   {
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": true,
     "python.formatting.provider": "black"
   }
   ```

2. **Recommended Extensions**:
   - Python
   - Pylint
   - Black Formatter
   - Git Lens

## Development Guidelines

### Code Style
- Follow PEP 8
- Use Black for formatting
- Maximum line length: 88 characters
- Docstrings: Google style

### Example:
```python
def process_input(text: str) -> Optional[str]:
    """Process user input and generate response.
    
    Args:
        text: The input text to process
        
    Returns:
        Optional[str]: The generated response or None if processing fails
        
    Raises:
        ValueError: If text is empty
    """
    if not text:
        raise ValueError("Input text cannot be empty")
    # Implementation
```

### Testing
1. **Unit Tests**:
   ```bash
   # Run all tests
   pytest tests/
   
   # Run specific test
   pytest tests/test_voice_processor.py
   
   # With coverage
   pytest --cov=src tests/
   ```

2. **Test Structure**:
   ```python
   def test_voice_processor_initialization():
       processor = VoiceProcessor()
       assert processor is not None
       assert processor._running is False
   ```

### Logging
- Use the Python logging module
- Log levels appropriately:
  - DEBUG: Detailed information
  - INFO: General operations
  - WARNING: Unexpected but handled
  - ERROR: Serious issues
  - CRITICAL: Application-breaking

Example:
```python
import logging

logger = logging.getLogger(__name__)

def initialize_component():
    try:
        logger.info("Initializing component...")
        # Implementation
        logger.debug("Component initialized with settings: %s", settings)
    except Exception as e:
        logger.error("Failed to initialize: %s", e)
        raise
```

## Component Development

### GUI Development
1. **Adding New Features**:
   ```python
   def add_feature(self):
       # 1. Add UI elements
       button = ttk.Button(self.main_frame, text="New Feature")
       
       # 2. Configure layout
       button.grid(row=0, column=0)
       
       # 3. Add event handling
       button.bind("<Button-1>", self.handle_feature)
   ```

2. **Theme Support**:
   ```python
   def apply_theme(self, widget):
       if self.settings["theme"] == "dark":
           widget.configure(
               background="#2b2b2b",
               foreground="#ffffff"
           )
   ```

### Voice Processor Development
1. **Audio Processing**:
   ```python
   async def process_audio(self, audio_data):
       try:
           # 1. Preprocess audio
           normalized = self.normalize_audio(audio_data)
           
           # 2. Convert to text
           text = await self.speech_to_text(normalized)
           
           # 3. Handle result
           await self.handle_recognition(text)
           
       except Exception as e:
           logger.error("Audio processing failed: %s", e)
   ```

2. **Error Recovery**:
   ```python
   def implement_recovery_strategy(self):
       # 1. Stop current processing
       self.stop_processing()
       
       # 2. Reset state
       self.reset_state()
       
       # 3. Reinitialize
       self.initialize_components()
   ```

### Assistant Development
1. **AI Integration**:
   ```python
   async def generate_response(self, input_text: str) -> str:
       messages = self._prepare_messages(input_text)
       
       response = await openai.ChatCompletion.acreate(
           model=self.settings["model"],
           messages=messages,
           temperature=self.settings["temperature"]
       )
       
       return response.choices[0].message.content
   ```

2. **State Management**:
   ```python
   def update_conversation_state(self, new_message: dict):
       # 1. Add to history
       self.conversation_history.append(new_message)
       
       # 2. Trim if needed
       self._trim_history()
       
       # 3. Update context
       self._update_context()
   ```

## Deployment

### Building
1. **Package Application**:
   ```bash
   # Create distribution
   python setup.py sdist bdist_wheel
   
   # Build standalone
   pyinstaller main.py
   ```

2. **Configuration**:
   ```bash
   # Production settings
   cp config/prod/* .
   
   # Set environment
   export SECONDBRAIN_ENV=production
   ```

### Testing
1. **Integration Tests**:
   ```bash
   pytest tests/integration/
   ```

2. **System Tests**:
   ```bash
   ./run_system_tests.sh
   ```

### Release Process
1. Version bump
2. Update changelog
3. Run test suite
4. Build distribution
5. Create release tag
6. Deploy

## Contributing

### Process
1. Fork repository
2. Create feature branch
3. Implement changes
4. Add tests
5. Update documentation
6. Submit pull request

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
Describe testing performed

## Documentation
List documentation updates
```

### Code Review
- Clean, documented code
- Passing tests
- Updated documentation
- Performance considerations
- Security review 