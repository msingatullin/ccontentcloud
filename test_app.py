#!/usr/bin/env python3
"""
Простое тестовое приложение для проверки порта
"""

import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'ok',
        'message': 'AI Content Orchestrator Test',
        'port': os.environ.get('PORT', 'not set')
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting test app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
