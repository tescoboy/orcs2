#!/usr/bin/env python3
"""Test Flask app with tenant routes."""

import os
os.environ['DATABASE_URL'] = 'sqlite:///./adcp.db'

from src.admin.app import create_app

def main():
    print("Creating Flask app...")
    app, socketio = create_app()
    print("✅ App created successfully")
    
    print("Testing tenant route...")
    with app.test_client() as client:
        response = client.get('/tenant/default/login')
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.data[:200]}")
        
        if response.status_code == 200:
            print("✅ Tenant route working!")
        else:
            print("❌ Tenant route failed")

if __name__ == "__main__":
    main()
