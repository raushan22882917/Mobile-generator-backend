# Google Cloud Run Deployment Guide

## Overview

On Google Cloud Run, the filesystem is **ephemeral** (temporary). Projects are stored in `/tmp` during generation and optionally uploaded to Google Cloud Storage for persistence.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Cloud Run Instance                    │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  /tmp/projects/                                    │ │
│  │  ├── project-abc-123/  (temporary)                 │ │
│  │  ├── project-def-456/  (temporary)                 │ │
│  │  └── project-ghi-789/  (temporary)                 │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                               │
│                          │ Upload after generation       │
│                          ▼                               │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│            Google Cloud Storage Bucket                   │
│                                                          │
│  gs://your-bucket/projects/                             │
│  ├── project-abc-123.zip  (persistent)                  │
│  ├── project-def-456.zip  (persistent)                  │
│  └── project-ghi-789.zip  (persistent)                  │
└─────────────────────────────────────────────────────────┘
```

## Configuration

### 1. Environment Variables

Update your `.env` or Cloud Run environment variables:

```env
# Required
OPENAI_API_KEY=your_openai_key
NGROK_AUTH_TOKEN=your_ngrok_token

# Cloud Run specific
PROJECTS_BASE_DIR=/tmp/projects
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_BUCKET=your-bucket-name

# Optional
API_KEY=your_api_key
REQUIRE_API_KEY=false
```

### 2. Create Cloud Storage Bucket

```bash
# Create bucket
gsutil mb gs://your-app-projects

# Set lifecycle (auto-delete old projects after 7 days)
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 7}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://your-app-projects
```

### 3. Update config.py

The config already supports environment variables:

```python
# In config.py
projects_base_dir: str = Field(
    default="./projects",
    description="Base directory for projects"
)
```

Set via environment:
```bash
export PROJECTS_BASE_DIR=/tmp/projects
```

## Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Expo CLI
RUN npm install -g expo-cli @expo/ngrok

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create /tmp/projects directory
RUN mkdir -p /tmp/projects

# Expose port
EXPOSE 8080

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## Cloud Build Configuration

Create `cloudbuild.yaml`:

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/mobile-generator-backend', '.']
  
  # Push the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/mobile-generator-backend']
  
  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'mobile-generator-backend'
      - '--image'
      - 'gcr.io/$PROJECT_ID/mobile-generator-backend'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--memory'
      - '4Gi'
      - '--cpu'
      - '2'
      - '--timeout'
      - '900'
      - '--max-instances'
      - '10'
      - '--set-env-vars'
      - 'PROJECTS_BASE_DIR=/tmp/projects,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_BUCKET=your-app-projects'
      - '--set-secrets'
      - 'OPENAI_API_KEY=openai-api-key:latest,NGROK_AUTH_TOKEN=ngrok-token:latest'

images:
  - 'gcr.io/$PROJECT_ID/mobile-generator-backend'
```

## Deployment Steps

### 1. Setup Google Cloud

```bash
# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    storage.googleapis.com
```

### 2. Create Secrets

```bash
# Create secrets
echo -n "your_openai_key" | gcloud secrets create openai-api-key --data-file=-
echo -n "your_ngrok_token" | gcloud secrets create ngrok-token --data-file=-

# Grant access to Cloud Run
gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding ngrok-token \
    --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 3. Deploy

```bash
# Deploy using Cloud Build
gcloud builds submit --config cloudbuild.yaml

# Or deploy directly
gcloud run deploy mobile-generator-backend \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 900 \
    --max-instances 10 \
    --set-env-vars PROJECTS_BASE_DIR=/tmp/projects \
    --set-secrets OPENAI_API_KEY=openai-api-key:latest,NGROK_AUTH_TOKEN=ngrok-token:latest
```

## Important Considerations

### 1. Ephemeral Storage

Cloud Run instances have **ephemeral storage**:
- `/tmp` is cleared when instance shuts down
- Maximum 10GB storage
- Projects are temporary

**Solution:** Upload to Cloud Storage after generation.

### 2. Instance Lifecycle

Cloud Run instances:
- Scale to zero when idle
- Start new instances on demand
- Have 15-minute request timeout

**Solution:** Use WebSocket for long-running operations.

### 3. Concurrent Requests

Cloud Run supports:
- Up to 1000 concurrent requests per instance
- Auto-scaling based on load

**Solution:** Set `max_concurrent_projects` appropriately.

### 4. Memory Limits

- Default: 512MB
- Recommended: 4GB for app generation
- Maximum: 32GB

**Solution:** Set `--memory 4Gi` in deployment.

## Project Storage Strategy

### Option 1: Temporary Only (Fastest)
```python
# In config.py
projects_base_dir = "/tmp/projects"
google_cloud_bucket = ""  # Empty = no upload
```

**Pros:**
- Fastest generation
- No storage costs

**Cons:**
- Projects lost on instance shutdown
- Can't download later

### Option 2: Upload to Cloud Storage (Recommended)
```python
# In config.py
projects_base_dir = "/tmp/projects"
google_cloud_bucket = "your-app-projects"
```

**Pros:**
- Projects persisted
- Can download anytime
- Automatic cleanup (lifecycle)

**Cons:**
- Slightly slower (upload time)
- Storage costs (~$0.02/GB/month)

### Option 3: Hybrid
```python
# Generate in /tmp
# Upload only on user request (download endpoint)
```

## Monitoring

### 1. Cloud Logging

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mobile-generator-backend" --limit 50
```

### 2. Cloud Monitoring

```bash
# View metrics
gcloud monitoring dashboards list
```

### 3. Health Check

```bash
# Check health
curl https://your-app.run.app/health
```

## Cost Optimization

### 1. Set Max Instances
```bash
--max-instances 10
```

### 2. Use Lifecycle Policies
```bash
# Auto-delete old projects after 7 days
gsutil lifecycle set lifecycle.json gs://your-bucket
```

### 3. Scale to Zero
Cloud Run automatically scales to zero when idle.

### 4. Use Spot Instances (Beta)
```bash
--execution-environment gen2
```

## Troubleshooting

### Issue: Out of Memory
```bash
# Increase memory
gcloud run services update mobile-generator-backend \
    --memory 8Gi
```

### Issue: Timeout
```bash
# Increase timeout (max 60 minutes)
gcloud run services update mobile-generator-backend \
    --timeout 3600
```

### Issue: Storage Full
```bash
# /tmp has 10GB limit
# Clean up old projects or upload to GCS
```

### Issue: Cold Start
```bash
# Set minimum instances
gcloud run services update mobile-generator-backend \
    --min-instances 1
```

## Testing Deployment

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe mobile-generator-backend \
    --region us-central1 \
    --format 'value(status.url)')

# Test health
curl $SERVICE_URL/health

# Test generation
curl -X POST $SERVICE_URL/api/v1/fast-generate \
    -H "Content-Type: application/json" \
    -d '{"prompt":"Create a todo app","user_id":"test"}'
```

## Best Practices

1. **Use /tmp for projects** - Ephemeral storage
2. **Upload to GCS** - For persistence
3. **Set memory to 4GB** - For npm install
4. **Set timeout to 900s** - For generation
5. **Use secrets** - For API keys
6. **Enable logging** - For debugging
7. **Set lifecycle** - Auto-cleanup
8. **Monitor costs** - Check billing

## Example: Complete Deployment

```bash
#!/bin/bash

# Variables
PROJECT_ID="your-project-id"
REGION="us-central1"
SERVICE_NAME="mobile-generator-backend"
BUCKET_NAME="your-app-projects"

# 1. Create bucket
gsutil mb gs://$BUCKET_NAME

# 2. Create secrets
echo -n "your_openai_key" | gcloud secrets create openai-api-key --data-file=-
echo -n "your_ngrok_token" | gcloud secrets create ngrok-token --data-file=-

# 3. Deploy
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 900 \
    --max-instances 10 \
    --set-env-vars PROJECTS_BASE_DIR=/tmp/projects,GOOGLE_CLOUD_BUCKET=$BUCKET_NAME \
    --set-secrets OPENAI_API_KEY=openai-api-key:latest,NGROK_AUTH_TOKEN=ngrok-token:latest

# 4. Get URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --format 'value(status.url)')

echo "Deployed to: $SERVICE_URL"
```

## Summary

- **Projects directory:** `/tmp/projects` (ephemeral)
- **Persistent storage:** Google Cloud Storage (optional)
- **Memory:** 4GB recommended
- **Timeout:** 900 seconds (15 minutes)
- **Auto-scaling:** Yes
- **Cost:** ~$0.10 per app generation

Your app is now ready for production on Google Cloud Run! 🚀
