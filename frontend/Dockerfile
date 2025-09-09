# Simple Dockerfile that builds from source
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source files
COPY src/ ./src/
COPY public/ ./public/

# Build the application
RUN npm run build

# Install nginx
RUN apk add --no-cache nginx

# Copy built files to nginx directory
RUN cp -r build/* /var/www/localhost/htdocs/

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Set permissions
RUN adduser -D -S -G www-data www-data && \
    chown -R www-data:www-data /var/www/localhost/htdocs && \
    chown -R www-data:www-data /var/cache/nginx && \
    chown -R www-data:www-data /var/log/nginx && \
    chown -R www-data:www-data /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R www-data:www-data /var/run/nginx.pid

# Switch to non-root user
USER www-data

# Expose port
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]