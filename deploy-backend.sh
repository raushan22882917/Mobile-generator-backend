#!/bin/bash
# Deploy backend to Google Cloud Run

set -e

echo "🚀 Deploying Mobile Generator Backend to Cloud Run..."
echo ""

# Configuration
PROJECT_ID="gen-lang-client-0148980288"
REGION="us-central1"
SERVICE_NAME="mobile-generator-backend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Set project
echo "📋 Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Build the Docker image
echo ""
echo "🔨 Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo ""
echo "🚢 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900 \
  --max-instances 10 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-env-vars="GOOGLE_CLOUD_BUCKET=${PROJECT_ID}-ai-expo-builder-archives" \
  --set-secrets="OPENAI_API_KEY=openai-api-key:latest" \
  --set-secrets="NGROK_AUTH_TOKEN=ngrok-auth-token:latest" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Your backend is now available at:"
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)"
