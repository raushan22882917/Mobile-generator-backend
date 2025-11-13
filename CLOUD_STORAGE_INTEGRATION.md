# Cloud Storage Integration - Complete

## ✅ What Was Implemented

Google Cloud Storage is now fully integrated for automatic project backup and retrieval.

## How It Works

### 1. During Generation
```
User submits prompt
    ↓
Project created in /tmp/projects/
    ↓
App generated (45-100 seconds)
    ↓
✅ Preview ready
    ↓
📤 Automatically uploaded to GCS
    ↓
✅ Complete
```

### 2. Storage Location

**Local (temporary):**
```
/tmp/projects/project-abc-123/
```

**Cloud Storage (permanent):**
```
gs://your-bucket/projects/project-abc-123.zip
```

## Configuration

### Environment Variables

```env
# Required for Cloud Storage
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_BUCKET=your-bucket-name

# Optional (auto-detected on Cloud Run)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Project directory
PROJECTS_BASE_DIR=/tmp/projects
```

### Example .env
```env
OPENAI_API_KEY=sk-...
NGROK_AUTH_TOKEN=2a...
GOOGLE_CLOUD_PROJECT=my-project-123
GOOGLE_CLOUD_BUCKET=my-app-projects
PROJECTS_BASE_DIR=/tmp/projects
```

## API Endpoints

### 1. Generate App (Auto-uploads)
```bash
POST /api/v1/fast-generate
```

Response includes GCS path:
```json
{
  "project_id": "abc-123",
  "preview_url": "https://abc.ngrok.io",
  "gcs_path": "gs://my-bucket/projects/abc-123.zip"
}
```

### 2. Download from Cloud Storage
```bash
GET /download-from-storage/{project_id}
```

Downloads ZIP directly from GCS.

### 3. Original Download (Local)
```bash
GET /download/{project_id}
```

Downloads from local filesystem (if still available).

## Features

### ✅ Automatic Upload
- Projects automatically uploaded after generation
- Non-blocking (doesn't slow down preview)
- Includes all files except node_modules

### ✅ Persistent Storage
- Projects survive instance restarts
- Available across all instances
- Automatic lifecycle management

### ✅ Download Anytime
- Download from GCS even if local copy is gone
- Works across different Cloud Run instances
- No need to regenerate

### ✅ Graceful Fallback
- If GCS not configured, works without it
- Projects still generated (just not uploaded)
- No errors if bucket unavailable

## Setup Guide

### 1. Create GCS Bucket

```bash
# Create bucket
gsutil mb gs://your-app-projects

# Set lifecycle (auto-delete after 7 days)
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

# Set CORS (if needed for direct downloads)
cat > cors.json << EOF
[
  {
    "origin": ["*"],
    "method": ["GET"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://your-app-projects
```

### 2. Set Permissions

```bash
# Grant Cloud Run service account access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

### 3. Deploy with Environment Variables

```bash
gcloud run deploy mobile-generator-backend \
    --source . \
    --region us-central1 \
    --memory 4Gi \
    --timeout 900 \
    --set-env-vars \
        PROJECTS_BASE_DIR=/tmp/projects,\
        GOOGLE_CLOUD_PROJECT=your-project-id,\
        GOOGLE_CLOUD_BUCKET=your-app-projects
```

## Code Changes

### Files Modified

1. **main.py**
   - Added `cloud_storage_manager` global
   - Initialize CloudStorageManager on startup
   - Pass to streaming generator

2. **services/streaming_generator.py**
   - Accept `cloud_storage_manager` parameter
   - Upload project after generation
   - Include `gcs_path` in response

3. **endpoints/streaming_generate.py**
   - Pass `cloud_storage_manager` to generator

4. **endpoints/fast_generate.py**
   - Pass `cloud_storage_manager` to generator

5. **endpoints/project_endpoints.py**
   - Added `/download-from-storage/{project_id}` endpoint

### Files Created

1. **services/cloud_storage_manager.py**
   - CloudStorageManager class
   - Upload/download methods
   - List/delete methods

## Usage Examples

### Frontend Integration

```javascript
// 1. Generate app
const response = await fetch('/api/v1/fast-generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: 'Create a todo app',
    user_id: 'user123'
  })
});

const { project_id, gcs_path } = await response.json();

console.log('Project uploaded to:', gcs_path);

// 2. Download from Cloud Storage (anytime, any instance)
const downloadUrl = `/download-from-storage/${project_id}`;
window.open(downloadUrl, '_blank');
```

### Check if Cloud Storage is Enabled

```javascript
// Check health endpoint
const health = await fetch('/health').then(r => r.json());

if (health.cloud_storage_enabled) {
  console.log('Cloud Storage is enabled');
  console.log('Bucket:', health.cloud_storage_bucket);
}
```

## Benefits

### 1. Persistence
- Projects survive instance restarts
- No data loss on scale-down
- Available across all instances

### 2. Scalability
- Multiple instances can access same projects
- No local storage limits
- Automatic cleanup via lifecycle

### 3. Cost Efficiency
- Only pay for storage used
- Automatic deletion of old projects
- ~$0.02/GB/month

### 4. Reliability
- Redundant storage (99.999999999% durability)
- Automatic backups
- Regional/multi-regional options

## Monitoring

### Check Upload Status

```bash
# List projects in bucket
gsutil ls gs://your-bucket/projects/

# Check project size
gsutil du -sh gs://your-bucket/projects/project-abc-123.zip

# View project metadata
gsutil stat gs://your-bucket/projects/project-abc-123.zip
```

### Logs

```bash
# View upload logs
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~'Uploading project'" --limit 10

# View download logs
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~'Downloading project'" --limit 10
```

## Cost Estimation

### Storage Costs
- **Storage:** $0.020/GB/month (Standard)
- **Operations:** $0.05 per 10,000 operations
- **Network:** Free within same region

### Example
- 100 projects/day
- 50MB average size
- 7-day retention

**Monthly cost:**
```
Storage: 100 * 30 * 0.05GB * $0.020 = $3.00
Operations: 100 * 30 * 2 / 10000 * $0.05 = $0.03
Total: ~$3/month
```

## Troubleshooting

### Issue: Upload Fails

**Check:**
1. Bucket exists: `gsutil ls gs://your-bucket`
2. Permissions: Service account has `storage.objectAdmin`
3. Logs: Check for error messages

**Solution:**
```bash
# Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:SERVICE_ACCOUNT" \
    --role="roles/storage.objectAdmin"
```

### Issue: Download Fails

**Check:**
1. Project exists in bucket
2. Blob name is correct
3. Permissions

**Solution:**
```bash
# Check if project exists
gsutil ls gs://your-bucket/projects/project-abc-123.zip

# Download manually to test
gsutil cp gs://your-bucket/projects/project-abc-123.zip ./test.zip
```

### Issue: Cloud Storage Not Detected

**Check:**
1. Environment variables set
2. Service account has permissions
3. Bucket exists

**Solution:**
```bash
# Verify environment
gcloud run services describe mobile-generator-backend \
    --region us-central1 \
    --format="value(spec.template.spec.containers[0].env)"
```

## Testing

### Local Testing

```bash
# Set environment variables
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_BUCKET=your-bucket-name
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Run server
uvicorn main:app --reload

# Test generation
curl -X POST http://localhost:8000/api/v1/fast-generate \
    -H "Content-Type: application/json" \
    -d '{"prompt":"Create a todo app","user_id":"test"}'

# Check bucket
gsutil ls gs://your-bucket/projects/
```

### Cloud Run Testing

```bash
# Deploy
gcloud run deploy mobile-generator-backend \
    --source . \
    --set-env-vars GOOGLE_CLOUD_BUCKET=your-bucket

# Test
SERVICE_URL=$(gcloud run services describe mobile-generator-backend \
    --region us-central1 --format='value(status.url)')

curl -X POST $SERVICE_URL/api/v1/fast-generate \
    -H "Content-Type: application/json" \
    -d '{"prompt":"Create a todo app","user_id":"test"}'

# Check bucket
gsutil ls gs://your-bucket/projects/
```

## Summary

✅ **Cloud Storage fully integrated**
- Automatic upload after generation
- Download from any instance
- Persistent storage
- Graceful fallback if not configured

🚀 **Ready for production on Google Cloud Run!**

---

**Configuration:**
```env
PROJECTS_BASE_DIR=/tmp/projects
GOOGLE_CLOUD_BUCKET=your-bucket-name
```

**That's it!** Projects are now automatically backed up to Cloud Storage.
