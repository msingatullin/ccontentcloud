# Simple Frontend Dockerfile for Google Cloud Run
FROM node:18-alpine AS build

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

# Build the application
RUN npm run build

# Production stage with serve
FROM node:18-alpine

# Install serve globally
RUN npm install -g serve

WORKDIR /app

# Copy built application
COPY --from=build /app/build ./build

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S -D -H -u 1001 -h /app -s /sbin/nologin -G nodejs -g nodejs nodejs && \
    chown -R nodejs:nodejs /app

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 8080

# Start serve
CMD ["serve", "-s", "build", "-l", "8080"]
