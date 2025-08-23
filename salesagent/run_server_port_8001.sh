#!/bin/bash

# orcs2 Server Startup Script (Port 8001)
# This script starts the orcs2 server on port 8001

set -e  # Exit on any error

echo "🚀 Starting orcs2 server on port 8001..."

# Check if we're in the right directory
if [ ! -f "src/admin/app.py" ]; then
    echo "❌ Error: Please run this script from the salesagent directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found. Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Set environment variables
export DATABASE_URL="sqlite:///./adcp.db"
export FLASK_ENV="development"

echo "🗄️  Database URL: $DATABASE_URL"
echo "📁 Working directory: $(pwd)"
echo "🌐 Port: 8001"

# Check if database exists
if [ ! -f "adcp.db" ]; then
    echo "❌ Error: Database file adcp.db not found"
    exit 1
fi

# Test if Flask app can be created
echo "🧪 Testing Flask app creation..."
python -c "from src.admin.app import create_app; app, socketio = create_app(); print('✅ Flask app created successfully')"

# Start the server
echo "🌐 Starting server on http://localhost:8001"
echo "📋 Available routes:"
echo "   - Buyer Portal: http://localhost:8001/buyer/"
echo "   - Publisher Login: http://localhost:8001/tenant/default/login"
echo "   - Health Check: http://localhost:8001/health"
echo ""
echo "🔄 Server is running... Press Ctrl+C to stop"
echo ""

# Start the Flask server
python -m flask --app src.admin.app:app run --host=0.0.0.0 --port=8001 --debug
