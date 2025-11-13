# Bucket Setup - appforge-projects

## ✅ Bucket Configuration

**Bucket Name:** `appforge-projects`  
**Location:** Multi-region (us)  
**Created:** Nov 5, 2025

## Configuration

### Environment Variables

```env
GOOGLE_CLOUD_BUCKET=appforge-projects
GOOGLE_CLOUD_PROJECT=your-project-id
PROJECTS_BASE_DIR=/tmp/projects
```

### Default Configuration

The bucket is now set as default in `config.py`:
```python
google_cloud_bucket: str = Field(
    default="appforge-projects",
    description="Google Cloud Storage bucket for project storage"
)
```

## Setup Steps

### 1. Set Lifecycle Policy (Optional)

Auto-delete old projects after 7 days:

```bash
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

gsutil lifecycle set lifecycle.json gs://appforge-projects
```

### 2. Set CORS (Optional)

For direct browser downloads:

```bash
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

gsutil cors set cors.json gs://appforge-projects
```

### 3. Grant Permissions

```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")

# Grant Cloud Run service account access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

## Deployment

### Cloud Run

```bash
gcloud run deploy mobile-generator-backend \
    --source . \
    --region us-central1 \
    --memory 4Gi \
    --timeout 900 \
    --set-env-vars \
        PROJECTS_BASE_DIR=/tmp/projects,\
        GOOGLE_CLOUD_BUCKET=appforge-projects
```

### Local Testing

```bash
# Set environment
export GOOGLE_CLOUD_BUCKET=appforge-projects
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Run server
uvicorn main:app --reload
```

## Verify Setup

### 1. Check Bucket Access

```bash
# List bucket contents
gsutil ls gs://appforge-projects/

# Test write access
echo "test" | gsutil cp - gs://appforge-projects/test.txt

# Test read access
gsutil cat gs://appforge-projects/test.txt

# Clean up
gsutil rm gs://appforge-projects/test.txt
```

### 2. Test Upload

```bash
# Generate an app
curl -X POST http://localhost:8000/api/v1/fast-generate \
    -H "Content-Type: application/json" \
    -d '{"prompt":"Create a todo app","user_id":"test"}'

# Check if uploaded
gsutil ls gs://appforge-projects/projects/
```

### 3. Test Download

```bash
# Get project ID from generation response
PROJECT_ID="abc-123-def-456"

# Download from Cloud Storage
curl http://localhost:8000/download-from-storage/$PROJECT_ID \
    -o project.zip
```

## Storage Structure

```
gs://appforge-projects/
└── projects/
    ├── project-abc-123.zip
    ├── project-def-456.zip
    └── project-ghi-789.zip
```

## Monitoring

### View Uploaded Projects

```bash
# List all projects
gsutil ls gs://appforge-projects/projects/

# Count projects
gsutil ls gs://appforge-projects/projects/ | wc -l

# Check total size
gsutil du -sh gs://appforge-projects/projects/
```

### View Recent Uploads

```bash
# List with timestamps
gsutil ls -l gs://appforge-projects/projects/

# Sort by date
gsutil ls -l gs://appforge-projects/projects/ | sort -k2
```

## Cost Estimation

**Bucket:** appforge-projects (Multi-region US)

### Storage Costs
- **Storage:** $0.026/GB/month (Multi-region)
- **Operations:** $0.05 per 10,000 operations
- **Network:** Free within same region

### Example (100 projects/day)
```
Storage: 100 * 30 * 0.05GB * $0.026 = $3.90/month
Operations: 100 * 30 * 2 / 10000 * $0.05 = $0.03/month
Total: ~$4/month
```

## Cleanup

### Delete Old Projects

```bash
# Delete projects older than 7 days (manual)
gsutil ls -l gs://appforge-projects/projects/ | \
    awk '{if ($2 < "2025-11-06") print $3}' | \
    xargs -I {} gsutil rm {}

# Or use lifecycle policy (automatic)
gsutil lifecycle set lifecycle.json gs://appforge-projects
```

### Delete All Projects

```bash
# Delete all projects (careful!)
gsutil -m rm gs://appforge-projects/projects/**
```

## Troubleshooting

### Issue: Permission Denied

```bash
# Check service account
gcloud run services describe mobile-generator-backend \
    --region us-central1 \
    --format="value(spec.template.spec.serviceAccountName)"

# Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:SERVICE_ACCOUNT" \
    --role="roles/storage.objectAdmin"
```

### Issue: Bucket Not Found

```bash
# Verify bucket exists
gsutil ls gs://appforge-projects

# Check bucket location
gsutil ls -L -b gs://appforge-projects
```

### Issue: Upload Fails

```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~'upload'" --limit 10

# Test manually
gsutil cp test.txt gs://appforge-projects/test.txt
```

## Summary

✅ **Bucket:** `appforge-projects`  
✅ **Location:** Multi-region (us)  
✅ **Default:** Set in config.py  
✅ **Ready:** For production use

### Quick Start

1. Set environment variable (optional, already default):
   ```bash
   export GOOGLE_CLOUD_BUCKET=appforge-projects
   ```

2. Deploy:
   ```bash
   gcloud run deploy mobile-generator-backend --source .
   ```

3. Projects automatically uploaded to:
   ```
   gs://appforge-projects/projects/
   ```

**That's it!** Your bucket is configured and ready to use. 🚀
