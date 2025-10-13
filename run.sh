#!/bin/bash
set -e

# Unset any environment variables that might override .env file
unset WP_APP_PASSWORD WP_USERNAME WP_BASE_URL GOOGLE_API_KEY

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch venv/.installed
fi

echo "Starting WordPress Auto Poster..."
echo "Server will be available at: http://127.0.0.1:8000"
echo "API documentation: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the application
uvicorn main:app --reload --host 127.0.0.1 --port 8000
