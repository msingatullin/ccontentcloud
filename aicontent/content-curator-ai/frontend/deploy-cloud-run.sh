#!/bin/bash

# Frontend Cloud Run Deployment Script
# AI Content Orchestrator

set -e

echo "🚀 AI Content Orchestrator Frontend Cloud Run Deployment"
echo "========================================================"

# Configuration
PROJECT_ID="content-curator-1755119514"
REGION="us-central1"
SERVICE_NAME="content-curator-frontend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
DOMAIN="goinvesting.ai"

echo "📋 Configuration:"
echo "  Project ID: ${PROJECT_ID}"
echo "  Region: ${REGION}"
echo "  Service: ${SERVICE_NAME}"
echo "  Image: ${IMAGE_NAME}"
echo "  Domain: ${DOMAIN}"
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run from frontend directory."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker."
    exit 1
fi

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: Not authenticated with gcloud. Please run 'gcloud auth login'"
    exit 1
fi

# Set project
echo "🔧 Setting Google Cloud project..."
gcloud config set project ${PROJECT_ID}

# Build the Docker image
echo "🏗️  Building Docker image..."
docker build -f Dockerfile.simple -t ${IMAGE_NAME}:latest .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed. Exiting."
    exit 1
fi

echo "✅ Docker image built successfully"

# Push to Google Container Registry
echo "📤 Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}:latest

if [ $? -ne 0 ]; then
    echo "❌ Docker push failed. Exiting."
    exit 1
fi

echo "✅ Image pushed successfully"

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --concurrency 80 \
    --set-env-vars "REACT_APP_API_URL=https://${DOMAIN}" \
    --set-env-vars "REACT_APP_API_BASE_URL=https://${DOMAIN}/api/v1" \
    --set-env-vars "REACT_APP_ENVIRONMENT=production" \
    --set-env-vars "REACT_APP_ENABLE_PWA=true" \
    --set-env-vars "REACT_APP_BILLING_ENABLED=true"

if [ $? -ne 0 ]; then
    echo "❌ Cloud Run deployment failed. Exiting."
    exit 1
fi

echo "✅ Frontend deployed successfully to Cloud Run"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")
echo "🌐 Service URL: ${SERVICE_URL}"

# Test the deployment
echo "🧪 Testing deployment..."
sleep 10

if curl -f -s "${SERVICE_URL}/health" > /dev/null; then
    echo "✅ Health check passed"
else
    echo "⚠️  Health check failed, but service might still be starting"
fi

if curl -f -s "${SERVICE_URL}" > /dev/null; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend is not accessible"
    exit 1
fi

echo ""
echo "🎉 Frontend deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "  1. Configure domain routing for ${DOMAIN}"
echo "  2. Set up SSL certificate"
echo "  3. Configure load balancer for API/Frontend routing"
echo ""
echo "🔗 Service URL: ${SERVICE_URL}"
echo "🏠 Domain: https://${DOMAIN}"
echo ""
echo "📊 To view logs:"
echo "  gcloud logs tail --service=${SERVICE_NAME} --region=${REGION}"
echo ""
echo "🔄 To update:"
echo "  ./deploy-cloud-run.sh"
