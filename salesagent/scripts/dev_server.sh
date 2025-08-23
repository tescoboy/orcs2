#!/bin/bash

# orcs2-salesagent Development Server Script
# This script starts the development server with proper environment setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the repo root
if [ ! -f "package.json" ] && [ ! -f "pyproject.toml" ] && [ ! -f "requirements.txt" ]; then
    print_error "This script must be run from the repository root directory"
    print_status "Please run: cd /path/to/orcs2-salesagent"
    exit 1
fi

print_success "Repository root detected"

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    print_warning "Virtual environment not detected"
    print_status "Please activate your virtual environment:"
    print_status "  source venv/bin/activate  # or source .venv/bin/activate"
    print_status "Then run this script again"
    exit 1
fi

print_success "Virtual environment active: $VIRTUAL_ENV"

# Load environment variables from .env if present
if [ -f ".env" ]; then
    print_status "Loading environment from .env file"
    export $(grep -v '^#' .env | xargs)
else
    print_warning "No .env file found"
    print_status "Create .env file with required environment variables"
fi

# Set default port if not specified
PORT=${PORT:-8000}
print_status "Using port: $PORT"

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port $PORT is already in use"
    print_status "You can:"
    print_status "  1. Kill the process using port $PORT"
    print_status "  2. Use a different port: PORT=8001 $0"
    print_status "  3. Find the process: lsof -i :$PORT"
    exit 1
fi

print_success "Port $PORT is available"

# Check if required Python packages are installed
print_status "Checking Python dependencies..."
if ! python -c "import flask, sqlalchemy" 2>/dev/null; then
    print_error "Required Python packages not found"
    print_status "Please install dependencies: pip install -r requirements.txt"
    exit 1
fi

print_success "Python dependencies OK"

# Start the development server
print_status "Starting development server..."
print_status "Server will be available at: http://localhost:$PORT"
print_status "Health check: http://localhost:$PORT/health"
print_status "Buyer UI: http://localhost:$PORT/buyer"
print_status ""
print_status "Press Ctrl+C to stop the server"
print_status ""

# Start Flask development server
python -m flask --app src.admin.app:app run --host=0.0.0.0 --port=$PORT --debug --reload
