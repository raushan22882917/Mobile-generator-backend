#!/bin/bash

# Setup Google Cloud Secrets for Cloud Run deployment
# Reads API keys from .env file automatically
# 
# Usage: ./setup-secrets.sh

PROJECT_ID="gen-lang-client-0148980288"

echo "Setting up secrets for project: $PROJECT_ID"
echo "Reading credentials from .env file..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found"
    exit 1
fi

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Check if environment variables are set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY not found in .env file"
    exit 1
fi

if [ -z "$NGROK_AUTH_TOKEN" ]; then
    echo "ERROR: NGROK_AUTH_TOKEN not found in .env file"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "ERROR: GEMINI_API_KEY not found in .env file"
    exit 1
fi

echo "✓ Credentials loaded from .env"

# Create secrets (if they don't exist)
echo "Creating secrets..."

# OpenAI API Key
echo -n "$OPENAI_API_KEY" | \
  gcloud secrets create openai-api-key \
    --data-file=- \
    --project=$PROJECT_ID \
    --replication-policy="automatic" 2>/dev/null || \
  echo -n "$OPENAI_API_KEY" | \
  gcloud secrets versions add openai-api-key \
    --data-file=- \
    --project=$PROJECT_ID

echo "✓ OpenAI API Key secret created/updated"

# Ngrok Auth Token
echo -n "$NGROK_AUTH_TOKEN" | \
  gcloud secrets create ngrok-auth-token \
    --data-file=- \
    --project=$PROJECT_ID \
    --replication-policy="automatic" 2>/dev/null || \
  echo -n "$NGROK_AUTH_TOKEN" | \
  gcloud secrets versions add ngrok-auth-token \
    --data-file=- \
    --project=$PROJECT_ID

echo "✓ Ngrok Auth Token secret created/updated"

# Gemini API Key
echo -n "$GEMINI_API_KEY" | \
  gcloud secrets create gemini-api-key \
    --data-file=- \
    --project=$PROJECT_ID \
    --replication-policy="automatic" 2>/dev/null || \
  echo -n "$GEMINI_API_KEY" | \
  gcloud secrets versions add gemini-api-key \
    --data-file=- \
    --project=$PROJECT_ID

echo "✓ Gemini API Key secret created/updated"

echo ""
echo "All secrets created successfully!"
echo ""
echo "Now you can deploy with: gcloud builds submit --config cloudbuild.yaml"
