#!/bin/bash
# Script to launch Streamlit app with virtual environment

VENV_PATH="./venv/bin/activate"
APP_SCRIPT="./src/main.py"

echo "Starting Knowledge Graph application..."
echo ""

# Check if virtual environment exists
if [ ! -f "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please create it with: python3 -m venv venv"
    read -p "Press enter to continue..."
    exit 1
fi

# Activate virtual environment
source "$VENV_PATH"
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment"
    read -p "Press enter to continue..."
    exit 1
fi

# Check if requirements are installed
if ! pip show streamlit &>/dev/null; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Run the Streamlit application
echo "Launching application..."
streamlit run "$APP_SCRIPT"