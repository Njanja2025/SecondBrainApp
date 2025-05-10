#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Set test environment variables
export STRIPE_TEST_MODE=true
export PAYMENT_CONFIG_PATH="config/test_payment_config.json"

# Run tests with verbose output
python -m pytest tests/test_payment_integration.py -v

# Check test results
if [ $? -eq 0 ]; then
    echo "All payment tests passed successfully!"
else
    echo "Some tests failed. Please check the output above for details."
fi 