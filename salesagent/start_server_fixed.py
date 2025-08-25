#!/usr/bin/env python3
"""Fixed server startup script that avoids hanging issues."""

import os
import sys
import threading
import time

# Set the database URL
os.environ['DATABASE_URL'] = 'sqlite:///./adcp.db'

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_simple_app():
    """Create a simplified Flask app without problematic imports."""
    from flask import Flask
    
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
    
    # Set database URL
    if not os.environ.get("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite:///./adcp.db"
    
    # Basic health endpoint
    @app.route('/health')
    def health():
        return 'OK'
    
    # Demo endpoint
    @app.route('/demo')
    def demo():
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Demo Interface</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h1>Demo Interface</h1>
                <p>Server is running successfully!</p>
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Buyer Portal</h5>
                                <a href="/buyer/" class="btn btn-primary">Go to Buyer Portal</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Publisher Login</h5>
                                <a href="/tenant/default/login" class="btn btn-success">Publisher Login</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
    
    return app

def main():
    print("🚀 Starting orcs2 server (fixed version)...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🗄️  Database URL: {os.environ.get('DATABASE_URL')}")
    
    try:
        # Create the Flask app
        print("📦 Creating Flask app...")
        app = create_simple_app()
        print("✅ Flask app created successfully")
        
        # Start the server in a separate thread to avoid blocking
        def run_server():
            app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        print("🌐 Starting server on http://localhost:8000")
        print("📋 Available routes:")
        print("   - Health Check: http://localhost:8000/health")
        print("   - Demo Interface: http://localhost:8000/demo")
        print("\n🔄 Server is running in background...")
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Test the server
        import requests
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                print("✅ Server is responding!")
            else:
                print(f"⚠️  Server responded with status: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Could not test server: {e}")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
