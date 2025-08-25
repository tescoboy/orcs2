#!/usr/bin/env python3
"""Working server that loads the real Flask application."""

import os
import sys
import time

# Set the database URL
os.environ['DATABASE_URL'] = 'sqlite:///./adcp.db'

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🚀 Starting real orcs2 server...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🗄️  Database URL: {os.environ.get('DATABASE_URL')}")
    
    try:
        # Import the real Flask app
        print("📦 Importing Flask app...")
        from src.admin.app import create_app
        
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
        print("   - Admin: http://localhost:8000/admin/")
        print("\n🔄 Server is running... Press Ctrl+C to stop")
        
        app.run(host='0.0.0.0', port=8000, debug=False)
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
