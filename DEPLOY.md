# Quick Deployment Guide

## Prerequisites
- Google Cloud SDK installed and authenticated
- Project ID: `gen-lang-client-0148980288`
- Artifact Registry repository created: `ai-expo-backend`

## Step 1: Setup Secrets (First Time Only)

The script automatically reads API keys from your `.env` file:

**Windows:**
```cmd
setup-secrets.cmd
```

**Linux/Mac:**
```bash
chmod +x setup-secrets.sh
./setup-secrets.sh
```

This creates three secrets in Google Cloud Secret Manager:
- `openai-api-key` - OpenAI API key for code generation
- `ngrok-auth-token` - Ngrok token for tunneling
- `gemini-api-key` - Google Gemini API key for image generation

**Note:** Make sure your `.env` file exists and contains the required keys before running the script.

## Step 2: Deploy to Cloud Run

```bash
gcloud builds submit --config cloudbuild.yaml
```

This will:
1. Build the Docker image
2. Push to Artifact Registry
3. Deploy to Cloud Run with all environment variables and secrets

## Step 3: Verify Deployment

After deployment completes, check the service URL:

```bash
gcloud run services describe ai-expo-backend --region=us-central1 --format="value(status.url)"
```

Test the API:
```bash
curl https://your-service-url.run.app/
```

Expected response:
```json
{
  "message": "AI Expo App Builder API",
  "version": "1.0.0",
  "status": "running"
}
```

## Configuration

The deployment uses these settings:
- **Memory**: 4Gi
- **CPU**: 2
- **Timeout**: 900 seconds (15 minutes)
- **Max Instances**: 2
- **Min Instances**: 0 (scales to zero)
- **Port**: 8080
- **Projects Directory**: `/tmp/projects` (ephemeral)
- **Cloud Storage**: `gen-lang-client-0148980288-ai-expo-builder-archives`

## Troubleshooting

### Container fails to start
Check logs:
```bash
gcloud run services logs read ai-expo-backend --region=us-central1 --limit=50
```

### Secrets not found
Verify secrets exist:
```bash
gcloud secrets list --project=gen-lang-client-0148980288
```

### Permission issues
Grant Cloud Run service account access to secrets:
```bash
gcloud projects add-iam-policy-binding gen-lang-client-0148980288 \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Update Deployment

To update after code changes:
```bash
gcloud builds submit --config cloudbuild.yaml
```

Cloud Run will automatically deploy the new version.

## Rollback

If deployment fails, rollback to previous version:
```bash
gcloud run services update-traffic ai-expo-backend \
  --region=us-central1 \
  --to-revisions=PREVIOUS_REVISION=100
```

List revisions:
```bash
gcloud run revisions list --service=ai-expo-backend --region=us-central1
```
