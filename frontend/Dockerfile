# Simple Dockerfile that builds from source
FROM node:18-alpine

WORKDIR /app

# Build arguments for React environment variables
ARG REACT_APP_API_URL=https://content-curator-1046574462613.us-central1.run.app
ARG VITE_API_URL=https://content-curator-1046574462613.us-central1.run.app

# Set environment variables for build
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source files
COPY src/ ./src/
COPY public/ ./public/

# Build the application with environment variables
RUN npm run build

# Install nginx
RUN apk add --no-cache nginx

# Copy built files to nginx directory
RUN mkdir -p /usr/share/nginx/html && cp -r build/* /usr/share/nginx/html/

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Set permissions - create all nginx directories
RUN mkdir -p /var/cache/nginx /var/log/nginx /etc/nginx/conf.d /run/nginx \
    /var/lib/nginx/tmp/client_body /var/lib/nginx/tmp/proxy \
    /var/lib/nginx/tmp/fastcgi /var/lib/nginx/tmp/uwsgi /var/lib/nginx/tmp/scgi \
    /var/lib/nginx/logs && \
    touch /run/nginx/nginx.pid && \
    chmod -R 755 /var/lib/nginx /var/cache/nginx /var/log/nginx /run/nginx /usr/share/nginx/html

# Run as root (simpler for Cloud Run)

# Expose port
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]