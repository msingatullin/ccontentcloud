#!/bin/sh

# Entrypoint script for Cloud Run
# Replace PORT variable in nginx.conf

# Get port from environment variable
PORT=${PORT:-8080}

# Create temporary nginx config with correct port
sed "s/8080/$PORT/g" /etc/nginx/nginx.conf > /tmp/nginx.conf

# Start nginx with temporary config
exec nginx -g "daemon off;" -c /tmp/nginx.conf
