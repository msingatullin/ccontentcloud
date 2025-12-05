"""
Gunicorn configuration file for AI Content Orchestrator
Optimized for Cloud Run deployment
"""
import os
import multiprocessing

# Bind to all interfaces on the PORT environment variable
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"

# Worker configuration
# Use sync workers for better compatibility with blocking operations
workers = int(os.environ.get('GUNICORN_WORKERS', '2'))
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Timeout configuration (important for Cloud Run)
timeout = 120  # 2 minutes - enough for initialization
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'content-curator-api'

# Preload application to speed up worker spawn
preload_app = False  # Set to False to avoid issues with DB connections

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
