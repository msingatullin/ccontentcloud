# Simple Dockerfile that builds from source
FROM node:18-alpine

WORKDIR /app

# Build arguments for React environment variables
ARG REACT_APP_API_URL=https://content-curator-dt3n7kzpwq-uc.a.run.app
ARG VITE_API_URL=https://content-curator-dt3n7kzpwq-uc.a.run.app

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
RUN cp -r build/* /var/www/localhost/htdocs/

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Set permissions
RUN adduser -D -S -G www-data www-data && \
    mkdir -p /var/cache/nginx /var/log/nginx /etc/nginx/conf.d /run/nginx && \
    chown -R www-data:www-data /var/www/localhost/htdocs && \
    chown -R www-data:www-data /var/cache/nginx && \
    chown -R www-data:www-data /var/log/nginx && \
    chown -R www-data:www-data /etc/nginx/conf.d && \
    chown -R www-data:www-data /run/nginx && \
    touch /run/nginx/nginx.pid && \
    chown -R www-data:www-data /run/nginx/nginx.pid

# Switch to non-root user
USER www-data

# Expose port
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]