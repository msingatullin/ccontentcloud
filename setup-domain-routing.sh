#!/bin/bash

# Domain Routing Setup Script
# AI Content Orchestrator - goinvesting.ai

set -e

echo "🌐 AI Content Orchestrator Domain Routing Setup"
echo "=============================================="

# Configuration
PROJECT_ID="content-curator-1755119514"
REGION="us-central1"
DOMAIN="goinvesting.ai"
BACKEND_SERVICE="content-curator"
FRONTEND_SERVICE="content-curator-frontend"

echo "📋 Configuration:"
echo "  Project ID: ${PROJECT_ID}"
echo "  Domain: ${DOMAIN}"
echo "  Backend: ${BACKEND_SERVICE}"
echo "  Frontend: ${FRONTEND_SERVICE}"
echo ""

# Check if we're authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: Not authenticated with gcloud. Please run 'gcloud auth login'"
    exit 1
fi

# Set project
echo "🔧 Setting Google Cloud project..."
gcloud config set project ${PROJECT_ID}

# Get service URLs
echo "🔍 Getting service URLs..."
BACKEND_URL=$(gcloud run services describe ${BACKEND_SERVICE} --region=${REGION} --format="value(status.url)")
FRONTEND_URL=$(gcloud run services describe ${FRONTEND_SERVICE} --region=${REGION} --format="value(status.url)")

echo "  Backend URL: ${BACKEND_URL}"
echo "  Frontend URL: ${FRONTEND_URL}"

# Create load balancer configuration
echo "🏗️  Creating load balancer configuration..."

cat > load-balancer.yaml << EOF
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: goinvesting-ssl-cert
  namespace: default
spec:
  domains:
    - goinvesting.ai
    - www.goinvesting.ai
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: goinvesting-ingress
  namespace: default
  annotations:
    kubernetes.io/ingress.global-static-ip-name: goinvesting-ip
    networking.gke.io/managed-certificates: goinvesting-ssl-cert
    kubernetes.io/ingress.class: "gce"
spec:
  rules:
  - host: goinvesting.ai
    http:
      paths:
      - path: /api/*
        pathType: ImplementationSpecific
        backend:
          service:
            name: backend-service
            port:
              number: 80
      - path: /*
        pathType: ImplementationSpecific
        backend:
          service:
            name: frontend-service
            port:
              number: 80
  - host: www.goinvesting.ai
    http:
      paths:
      - path: /api/*
        pathType: ImplementationSpecific
        backend:
          service:
            name: backend-service
            port:
              number: 80
      - path: /*
        pathType: ImplementationSpecific
        backend:
          service:
            name: frontend-service
            port:
              number: 80
EOF

echo "✅ Load balancer configuration created: load-balancer.yaml"

# Create Cloud Run service mappings
echo "🔗 Creating Cloud Run service mappings..."

cat > cloud-run-services.yaml << EOF
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: default
spec:
  type: ExternalName
  externalName: ${BACKEND_URL#https://}
  ports:
  - port: 80
    targetPort: 443
    protocol: TCP
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: default
spec:
  type: ExternalName
  externalName: ${FRONTEND_URL#https://}
  ports:
  - port: 80
    targetPort: 443
    protocol: TCP
EOF

echo "✅ Cloud Run service mappings created: cloud-run-services.yaml"

# Reserve static IP
echo "🌐 Reserving static IP address..."
gcloud compute addresses create goinvesting-ip --global --ip-version IPV4 || echo "IP already exists"

# Get the IP address
IP_ADDRESS=$(gcloud compute addresses describe goinvesting-ip --global --format="value(address)")
echo "📍 Static IP: ${IP_ADDRESS}"

echo ""
echo "🎉 Domain routing configuration completed!"
echo ""
echo "📋 Next steps:"
echo "  1. Update DNS records for ${DOMAIN} to point to: ${IP_ADDRESS}"
echo "  2. Deploy the load balancer configuration:"
echo "     kubectl apply -f cloud-run-services.yaml"
echo "     kubectl apply -f load-balancer.yaml"
echo "  3. Wait for SSL certificate provisioning (can take up to 15 minutes)"
echo ""
echo "🔗 Current service URLs:"
echo "  Frontend: ${FRONTEND_URL}"
echo "  Backend: ${BACKEND_URL}"
echo ""
echo "🌐 After DNS setup:"
echo "  https://${DOMAIN} → Frontend (Landing Page)"
echo "  https://${DOMAIN}/api → Backend API"
echo ""
echo "📊 To check status:"
echo "  kubectl get managedcertificate"
echo "  kubectl get ingress"
echo "  kubectl describe ingress goinvesting-ingress"
