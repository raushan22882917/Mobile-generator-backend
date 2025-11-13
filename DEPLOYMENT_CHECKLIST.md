# Deployment Checklist

## ✅ Pre-Deployment

### 1. Configuration
- [x] Bucket configured: `appforge-projects`
- [ ] Environment variables set
- [ ] API keys configured
- [ ] Ngrok token set

### 2. Environment Variables

```env
# Required
OPENAI_API_KEY=your_key
NGROK_AUTH_TOKEN=your_token

# Cloud Storage (default: appforge-projects)
GOOGLE_CLOUD_BUCKET=appforge-projects
GOOGLE_CLOUD_PROJECT=your-project-id

# Paths (for Cloud Run)
PROJECTS_BASE_DIR=/tmp/projects
```

### 3. Bucket Setup
- [x] Bucket exists: `appforge-projects`
- [ ] Lifecycle policy set (optional)
- [ ] CORS configured (optional)
- [ ] Permissions granted

## 🚀 Deployment

### Option 1: Quick Deploy

```bash
gcloud run deploy mobile-generator-backend \
    --source . \
    --region us-central1 \
    --memory 4Gi \
    --timeout 900 \
    --allow-unauthenticated
```

### Option 2: With Environment Variables

```bash
gcloud run deploy mobile-generator-backend \
    --source . \
    --region us-central1 \
    --memory 4Gi \
    --timeout 900 \
    --allow-unauthenticated \
    --set-env-vars \
        PROJECTS_BASE_DIR=/tmp/projects,\
        GOOGLE_CLOUD_BUCKET=appforge-projects \
    --set-secrets \
        OPENAI_API_KEY=openai-api-key:latest,\
        NGROK_AUTH_TOKEN=ngrok-token:latest
```

## ✅ Post-Deployment

### 1. Verify Deployment

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe mobile-generator-backend \
    --region us-central1 \
    --format='value(status.url)')

echo "Service URL: $SERVICE_URL"
```

### 2. Test Health

```bash
curl $SERVICE_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-13T...",
  "active_projects": 0,
  "cloud_storage_enabled": true,
  "cloud_storage_bucket": "appforge-projects"
}
```

### 3. Test Generation

```bash
curl -X POST $SERVICE_URL/api/v1/fast-generate \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "Create a simple todo list app",
        "user_id": "test-user"
    }'
```

Expected response:
```json
{
  "project_id": "abc-123-def-456",
  "status": "processing",
  "message": "Generation started...",
  "websocket_url": "/api/v1/ws/generate/abc-123-def-456"
}
```

### 4. Verify Cloud Storage

```bash
# Wait 2-3 minutes for generation to complete

# Check bucket
gsutil ls gs://appforge-projects/projects/

# Should see: gs://appforge-projects/projects/abc-123-def-456.zip
```

### 5. Test Download

```bash
# Download from Cloud Storage
curl $SERVICE_URL/download-from-storage/abc-123-def-456 \
    -o test-project.zip

# Verify ZIP file
unzip -l test-project.zip
```

## 📊 Monitoring

### View Logs

```bash
# Real-time logs
gcloud run services logs tail mobile-generator-backend \
    --region us-central1

# Recent logs
gcloud logging read \
    "resource.type=cloud_run_revision AND resource.labels.service_name=mobile-generator-backend" \
    --limit 50
```

### Check Metrics

```bash
# View in Cloud Console
gcloud run services describe mobile-generator-backend \
    --region us-central1
```

### Monitor Storage

```bash
# Check bucket size
gsutil du -sh gs://appforge-projects/

# Count projects
gsutil ls gs://appforge-projects/projects/ | wc -l

# View recent uploads
gsutil ls -l gs://appforge-projects/projects/ | tail -10
```

## 🔧 Configuration Summary

### Current Setup

| Setting | Value |
|---------|-------|
| **Bucket** | `appforge-projects` |
| **Location** | Multi-region (us) |
| **Projects Dir** | `/tmp/projects` |
| **Memory** | 4Gi |
| **Timeout** | 900s (15 min) |
| **Region** | us-central1 |

### API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/fast-generate` | Start generation |
| `GET /project-status/{id}` | Check status |
| `GET /download-from-storage/{id}` | Download from GCS |
| `WS /api/v1/ws/generate/{id}` | Real-time updates |

## 🎯 Success Criteria

- [ ] Service deployed successfully
- [ ] Health check returns 200
- [ ] Can generate test app
- [ ] Project uploaded to GCS
- [ ] Can download from GCS
- [ ] WebSocket connects
- [ ] Real-time updates work
- [ ] Preview URL accessible

## 📚 Documentation

- **API_DOCUMENTATION.md** - Complete API reference
- **CLOUD_STORAGE_INTEGRATION.md** - Storage details
- **BUCKET_SETUP.md** - Bucket configuration
- **CLOUD_RUN_DEPLOYMENT.md** - Deployment guide

## 🆘 Troubleshooting

### Issue: Deployment Fails

```bash
# Check build logs
gcloud builds list --limit 5

# View specific build
gcloud builds log BUILD_ID
```

### Issue: Health Check Fails

```bash
# Check service status
gcloud run services describe mobile-generator-backend \
    --region us-central1

# View logs
gcloud run services logs tail mobile-generator-backend
```

### Issue: Storage Upload Fails

```bash
# Check permissions
gcloud projects get-iam-policy PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.role:roles/storage.objectAdmin"

# Test bucket access
gsutil ls gs://appforge-projects/
```

## 📞 Support

If issues persist:
1. Check logs: `gcloud run services logs tail`
2. Verify environment variables
3. Test bucket access manually
4. Review error messages

## ✅ Final Checklist

- [ ] Deployed to Cloud Run
- [ ] Health check passes
- [ ] Test generation works
- [ ] Projects upload to GCS
- [ ] Download from GCS works
- [ ] Frontend connected
- [ ] Monitoring enabled
- [ ] Documentation reviewed

---

**Status:** Ready for Production 🚀

**Bucket:** `appforge-projects`  
**Region:** us-central1  
**Memory:** 4Gi  
**Timeout:** 900s

**All systems configured and ready to deploy!**
