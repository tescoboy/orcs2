#!/usr/bin/env python3
"""Simple server that runs in foreground to debug issues."""

from flask import Flask

app = Flask(__name__)

@app.route('/health')
def health():
    return 'OK'

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
            <div class="alert alert-success">
                <strong>Success!</strong> The server is working without hanging.
            </div>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("🚀 Starting simple server...")
    print("🌐 Server will be available at http://localhost:8000")
    print("📋 Endpoints:")
    print("   - Health: http://localhost:8000/health")
    print("   - Demo: http://localhost:8000/demo")
    print("✅ Server started successfully!")
    
    app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)
