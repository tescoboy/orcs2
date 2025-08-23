#!/usr/bin/env python3
"""Simple server startup script."""

import os
import sys

# Set the database URL
os.environ['DATABASE_URL'] = 'sqlite:///./adcp.db'

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.admin.app import create_app

def main():
    print("🚀 Starting orcs2 server...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🗄️  Database URL: {os.environ.get('DATABASE_URL')}")
    
    try:
        # Create the Flask app
        print("📦 Creating Flask app...")
        app, socketio = create_app()
        print("✅ Flask app created successfully")
        
        # Start the server
        print("🌐 Starting server on http://localhost:8000")
        print("📋 Available routes:")
        print("   - Buyer Portal: http://localhost:8000/buyer/")
        print("   - Publisher Login: http://localhost:8000/tenant/default/login")
        print("   - Health Check: http://localhost:8000/health")
        print("\n🔄 Server is running... Press Ctrl+C to stop")
        
        app.run(host='0.0.0.0', port=8000, debug=True)
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
