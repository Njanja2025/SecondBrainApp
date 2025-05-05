# SecondBrain Assistant User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Voice Interaction](#voice-interaction)
4. [Keyboard Shortcuts](#keyboard-shortcuts)
5. [Configuration](#configuration)
6. [Tips & Tricks](#tips--tricks)
7. [Troubleshooting](#troubleshooting)

## Getting Started

### First Launch
1. After installation, launch SecondBrain:
   ```bash
   python3 main.py
   ```
2. The application will request necessary permissions:
   - Microphone access
   - System notifications (optional)

### Interface Overview
- **Conversation Area**: Main display for interaction history
- **Input Field**: Type messages or view voice transcription
- **Status Bar**: Shows system status and notifications
- **Menu Bar**: Access to all features and settings

## Basic Usage

### Text Input
1. Click the input field or press `Tab` to focus
2. Type your message
3. Press `Enter` or click "Send"

### Voice Input
1. Ensure microphone is enabled (🎤 icon in status bar)
2. Speak naturally - the system will automatically:
   - Detect speech
   - Transcribe to text
   - Process your request
   - Respond via voice and text

### Managing Conversations
- **Save**: Use `Ctrl/Cmd + S` or File > Save Conversation
- **Clear**: Use `Ctrl/Cmd + L` or File > Clear Conversation
- **Copy**: Select text and use `Ctrl/Cmd + C`

## Voice Interaction

### Best Practices
1. **Environment**:
   - Quiet surroundings
   - Minimal background noise
   - Close to microphone

2. **Speaking**:
   - Clear, natural speech
   - Normal pace
   - Brief pauses between sentences

3. **Commands**:
   - "Stop listening" - Temporarily disable voice input
   - "Start listening" - Re-enable voice input
   - "Clear conversation" - Clear the chat history
   - "Save conversation" - Save current session

### Voice Settings
Access through Voice Control Panel:
1. **Voice Selection**:
   - Choose from available system voices
   - Adjust speaking rate
   - Set volume level

2. **Recognition Settings**:
   - Sensitivity adjustment
   - Noise threshold
   - Response delay

## Keyboard Shortcuts

### Global Shortcuts
- `Ctrl/Cmd + Shift + V`: Toggle voice input
- `Ctrl/Cmd + L`: Clear conversation
- `Ctrl/Cmd + S`: Save conversation
- `Ctrl/Cmd + T`: Toggle theme
- `Ctrl/Cmd + Q`: Quit application
- `F1`: Show help

### Text Editing
- `Enter`: Send message
- `Ctrl/Cmd + Z`: Undo typing
- `Ctrl/Cmd + Shift + Z`: Redo typing
- `Ctrl/Cmd + A`: Select all text
- `Ctrl/Cmd + X`: Cut selected text
- `Ctrl/Cmd + C`: Copy selected text
- `Ctrl/Cmd + V`: Paste text

## Configuration

### GUI Settings (`gui_settings.json`)
```json
{
    "theme": "light",
    "font_size": 12,
    "max_history": 100,
    "window": {
        "width": 800,
        "height": 600,
        "position": "center"
    }
}
```

### Voice Settings (`voice_processor_settings.json`)
```json
{
    "energy_threshold": 4000,
    "dynamic_energy_threshold": true,
    "pause_threshold": 0.8,
    "phrase_threshold": 0.3
}
```

### Assistant Settings (`assistant_settings.json`)
```json
{
    "model": "gpt-4-turbo-preview",
    "temperature": 0.7,
    "max_history": 10
}
```

## Tips & Tricks

### Optimizing Voice Recognition
1. **Calibration**:
   - Run in quiet environment first
   - Let system adjust to ambient noise
   - Speak test phrases

2. **Performance**:
   - Keep conversation history manageable
   - Clear history periodically
   - Use push-to-talk for noisy environments

### Customization
1. **Theme Switching**:
   - Automatic dark mode with system
   - Custom color schemes
   - Font adjustments

2. **Workflow**:
   - Save common responses
   - Create custom shortcuts
   - Use text expansion

## Troubleshooting

### Common Issues

1. **Voice Recognition Problems**:
   - Check microphone permissions
   - Verify input device selection
   - Adjust sensitivity settings
   - Test in system sound settings

2. **Performance Issues**:
   - Clear conversation history
   - Check CPU/memory usage
   - Restart application
   - Update dependencies

3. **API Connection**:
   - Verify internet connection
   - Check API key validity
   - Review rate limits
   - Check error logs

### Error Messages

1. **"Microphone not found"**:
   - Check physical connection
   - Verify system permissions
   - Select correct input device

2. **"API Error"**:
   - Verify API key
   - Check internet connection
   - Review quota/limits

3. **"Voice output failed"**:
   - Check system volume
   - Verify voice selection
   - Review voice settings

### Getting Help

1. **Documentation**:
   - Check this user guide
   - Review README.md
   - Check online documentation

2. **Support**:
   - GitHub issues
   - Email support
   - Community forums

3. **Updates**:
   - Check version number
   - Review changelog
   - Install updates 