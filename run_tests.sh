#!/bin/bash

# Set python path for src to be recognized in tests
export PYTHONPATH=src

# Run tests with verbose and asyncio support, disable warnings
pytest tests/ --disable-warnings -v