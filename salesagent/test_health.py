#!/usr/bin/env python3
"""Test health endpoint."""

import os
os.environ['DATABASE_URL'] = 'sqlite:///./adcp.db'

from src.admin.app import create_app

def main():
    print("Testing health endpoint...")
    
    try:
        app, socketio = create_app()
        print("✅ App created successfully")
        
        with app.test_client() as client:
            response = client.get('/health')
            print(f"Health endpoint status: {response.status_code}")
            print(f"Response: {response.data[:200]}")
            
            if response.status_code == 200:
                print("✅ Health endpoint working!")
            else:
                print("❌ Health endpoint failed")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
