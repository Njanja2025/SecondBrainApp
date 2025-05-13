#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Run the tests
python test_launch.py

# Check the exit status
if [ $? -eq 0 ]; then
    echo "All tests passed! System is ready for launch."
else
    echo "Some tests failed. Please check the logs for details."
fi 