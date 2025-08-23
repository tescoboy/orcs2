#!/usr/bin/env python3
"""Minimal Flask server test."""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/test')
def test():
    return 'Test endpoint working!'

if __name__ == '__main__':
    print("Starting minimal Flask server...")
    app.run(host='0.0.0.0', port=8000, debug=True)
