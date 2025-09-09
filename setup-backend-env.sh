#!/bin/bash

# Backend Environment Variables Setup Script
# AI Content Orchestrator - Cloud Run

set -e

echo "🔧 AI Content Orchestrator Backend Environment Setup"
echo "=================================================="

# Configuration
PROJECT_ID="content-curator-1755119514"
REGION="us-central1"
SERVICE_NAME="content-curator"

echo "📋 Configuration:"
echo "  Project ID: ${PROJECT_ID}"
echo "  Service: ${SERVICE_NAME}"
echo "  Region: ${REGION}"
echo ""

# Check if we're authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: Not authenticated with gcloud. Please run 'gcloud auth login'"
    exit 1
fi

# Set project
echo "🔧 Setting Google Cloud project..."
gcloud config set project ${PROJECT_ID}

# Generate secure secrets
echo "🔐 Generating secure secrets..."
JWT_SECRET=$(openssl rand -base64 32)
REFRESH_SECRET=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 32)

echo "✅ Secrets generated"

# Update Cloud Run service with environment variables
echo "🚀 Updating Cloud Run service with environment variables..."

gcloud run services update ${SERVICE_NAME} \
    --region=${REGION} \
    --set-env-vars="ENVIRONMENT=production" \
    --set-env-vars="SECRET_KEY=${SECRET_KEY}" \
    --set-env-vars="JWT_SECRET_KEY=${JWT_SECRET}" \
    --set-env-vars="REFRESH_TOKEN_SECRET_KEY=${REFRESH_SECRET}" \
    --set-env-vars="JWT_ACCESS_TOKEN_EXPIRES_MINUTES=30" \
    --set-env-vars="JWT_REFRESH_TOKEN_EXPIRES_DAYS=7" \
    --set-env-vars="DATABASE_URL=sqlite:///./content_curator_prod.db" \
    --set-env-vars="EMAIL_VERIFICATION_TOKEN_EXPIRES_HOURS=24" \
    --set-env-vars="SMTP_SERVER=smtp.gmail.com" \
    --set-env-vars="SMTP_PORT=587" \
    --set-env-vars="SENDER_EMAIL=noreply@goinvesting.ai" \
    --set-env-vars="YOOKASSA_SHOP_ID=1134145" \
    --set-env-vars="YOOKASSA_SECRET_KEY=live_144m9a57yZytkuyh90IAiM0sQoF-L3SAyfB4hZMSDFk" \
    --set-env-vars="YOOKASSA_TEST_MODE=false" \
    --set-env-vars="YOOKASSA_RETURN_URL=https://goinvesting.ai/billing/success" \
    --set-env-vars="YOOKASSA_CANCEL_URL=https://goinvesting.ai/billing/cancel" \
    --set-env-vars="BILLING_DEFAULT_TRIAL_DAYS=14" \
    --set-env-vars="BILLING_AUTO_RENEW_ENABLED=true" \
    --set-env-vars="BILLING_NOTIFICATIONS_ENABLED=true" \
    --set-env-vars="API_BASE_URL=https://goinvesting.ai" \
    --set-env-vars="CORS_ORIGINS=https://goinvesting.ai" \
    --set-env-vars="LOG_LEVEL=INFO" \
    --set-env-vars="BCRYPT_ROUNDS=12" \
    --set-env-vars="RATE_LIMIT_ENABLED=true" \
    --set-env-vars="RATE_LIMIT_REQUESTS_PER_MINUTE=100" \
    --set-env-vars="MAX_CONTENT_LENGTH=16777216" \
    --set-env-vars="CACHE_TYPE=simple" \
    --set-env-vars="CACHE_DEFAULT_TIMEOUT=300" \
    --set-env-vars="HEALTH_CHECK_ENABLED=true"

if [ $? -ne 0 ]; then
    echo "❌ Failed to update environment variables"
    exit 1
fi

echo "✅ Environment variables updated successfully"

# Test the service
echo "🧪 Testing the service..."
sleep 10

# Test health endpoint
if curl -f -s "https://goinvesting.ai/health" > /dev/null; then
    echo "✅ Health check passed"
else
    echo "⚠️  Health check failed, but service might still be starting"
fi

# Test auth endpoints
echo "🔐 Testing auth endpoints..."

# Test auth status
if curl -f -s "https://goinvesting.ai/api/v1/auth/status" > /dev/null; then
    echo "✅ Auth status endpoint working"
else
    echo "❌ Auth status endpoint failed"
fi

echo ""
echo "🎉 Backend environment setup completed!"
echo ""
echo "📋 Environment variables configured:"
echo "  ✅ JWT_SECRET_KEY: Generated"
echo "  ✅ REFRESH_TOKEN_SECRET_KEY: Generated"
echo "  ✅ SECRET_KEY: Generated"
echo "  ✅ DATABASE_URL: SQLite"
echo "  ✅ YooKassa: Configured"
echo "  ✅ Email: Configured"
echo "  ✅ CORS: Configured"
echo ""
echo "🔗 Service URL: https://goinvesting.ai"
echo "📊 To view logs:"
echo "  gcloud logs tail --service=${SERVICE_NAME} --region=${REGION}"
echo ""
echo "🧪 To test registration:"
echo "  curl -X POST https://goinvesting.ai/api/v1/auth/register \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"test@example.com\",\"password\":\"testpass123\"}'"
