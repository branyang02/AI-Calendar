#!/bin/bash

# Define the virtual environment directory name
VENV_DIR="venv"

# Ensure the virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Run Django server
echo "Starting Django server..."
python manage.py runserver
