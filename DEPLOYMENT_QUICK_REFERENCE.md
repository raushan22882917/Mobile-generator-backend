# Deployment Quick Reference

## Google Cloud Run

### Project Directory
```
/tmp/projects/
```

### Why /tmp?
- Cloud Run filesystem is **ephemeral** (temporary)
- `/tmp` is the only writable directory (max 10GB)
- Projects are cleared when instance shuts down

### Environment Variables
```env
PROJECTS_BASE_DIR=/tmp/projects
GOOGLE_CLOUD_BUCKET=your-bucket-name
GOOGLE_CLOUD_PROJECT=your-project-id
```

### Deploy Command
```bash
gcloud run deploy mobile-generator-backend \
    --source . \
    --region us-central1 \
    --memory 4Gi \
    --timeout 900 \
    --set-env-vars PROJECTS_BASE_DIR=/tmp/projects
```

### Storage Strategy

#### Option 1: Temporary Only
- Projects in `/tmp` only
- Fastest
- Lost on shutdown

#### Option 2: With Cloud Storage (Recommended)
- Projects in `/tmp` during generation
- Uploaded to GCS after completion
- Persistent
- Can download anytime

### Complete Setup

```bash
# 1. Set environment
export PROJECTS_BASE_DIR=/tmp/projects
export GOOGLE_CLOUD_BUCKET=your-app-projects

# 2. Create bucket
gsutil mb gs://your-app-projects

# 3. Deploy
gcloud run deploy mobile-generator-backend \
    --source . \
    --region us-central1 \
    --memory 4Gi \
    --timeout 900 \
    --set-env-vars PROJECTS_BASE_DIR=/tmp/projects,GOOGLE_CLOUD_BUCKET=your-app-projects
```

## Local Development

### Project Directory
```
./projects/
```

### Environment Variables
```env
PROJECTS_BASE_DIR=./projects
```

### Run
```bash
uvicorn main:app --reload
```

## Key Differences

| Aspect | Local | Cloud Run |
|--------|-------|-----------|
| Directory | `./projects/` | `/tmp/projects/` |
| Persistence | Permanent | Temporary |
| Storage | Local disk | Cloud Storage |
| Cleanup | Manual | Automatic |

## Files Created

1. `services/cloud_storage_manager.py` - GCS integration
2. `CLOUD_RUN_DEPLOYMENT.md` - Complete guide
3. `DEPLOYMENT_QUICK_REFERENCE.md` - This file

## Next Steps

1. Read `CLOUD_RUN_DEPLOYMENT.md` for complete guide
2. Set `PROJECTS_BASE_DIR=/tmp/projects` in Cloud Run
3. Create GCS bucket for persistence (optional)
4. Deploy!

---

**Summary:** Use `/tmp/projects/` on Cloud Run, optionally upload to GCS for persistence.
