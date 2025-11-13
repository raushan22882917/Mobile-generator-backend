# Deploy Updates - Cloud Storage Project Listing

## Changes Made

### 1. Updated `/projects` Endpoint
- Now lists projects from **both** local storage AND Cloud Storage
- Returns counts for local and cloud projects separately
- Shows source of each project (local or cloud_storage)

### 2. Added CloudStorageManager Methods
- `list_projects()` - Lists all projects in GCS bucket
- `get_project_metadata()` - Gets metadata for a specific project (size, dates, etc.)

### 3. Response Format
```json
{
  "projects": [
    {
      "id": "project-id",
      "name": "project-name",
      "status": "archived",
      "source": "cloud_storage",
      "created_at": "2024-11-13T10:00:00",
      "last_active": "2024-11-13T10:00:00",
      "is_active": false
    }
  ],
  "total": 4,
  "local_count": 0,
  "cloud_count": 4
}
```

## How to Deploy

### Option 1: Using Cloud Build (Recommended)
```bash
gcloud builds submit --config cloudbuild.yaml
```

### Option 2: Using deploy script
**Windows:**
```cmd
deploy-backend.cmd
```

**Linux/Mac:**
```bash
chmod +x deploy-backend.sh
./deploy-backend.sh
```

## Verify Deployment

After deployment completes (takes ~5-10 minutes):

### 1. Check service is running:
```bash
gcloud run services describe mobile-generator-backend --region=us-central1
```

### 2. Test the endpoint:
```bash
curl https://mobile-generator-backend-1098053868371.us-central1.run.app/projects
```

### 3. Run test script:
```bash
python test_cloud_projects.py
```

Expected output:
```
📊 Total Projects: 4
📁 Local Projects: 0
☁️  Cloud Projects: 4

📋 Projects List:
1. 18dc13ac-a7e3-4832-9bc6-dbdcdb5937bb
   Status: archived
   Source: cloud_storage
   Created: 2024-11-13T10:00:00
   Active: False
...
```

## Current Cloud Storage Projects

Based on bucket scan, you have **4 projects**:
1. `18dc13ac-a7e3-4832-9bc6-dbdcdb5937bb.zip`
2. `2687f80f-9513-49b8-ab02-0736b40157ea.zip`
3. `625ce62f-c494-4fbf-806a-1b2e7a422876.zip`
4. `b6a1c5e6-128e-44e9-b26c-0e0448630f5b.zip`

These will be visible in the `/projects` endpoint after deployment.

## Files Modified

1. `main.py` - Updated `/projects` endpoint
2. `services/cloud_storage_manager.py` - Added list and metadata methods
3. `test_cloud_projects.py` - Test script (new)

## Troubleshooting

### Projects still not showing after deployment

1. Check Cloud Run logs:
```bash
gcloud run services logs read mobile-generator-backend --region=us-central1 --limit=50
```

2. Verify bucket access:
```bash
gcloud storage ls gs://gen-lang-client-0148980288-ai-expo-builder-archives/projects/
```

3. Check service account permissions:
```bash
gcloud projects get-iam-policy gen-lang-client-0148980288 \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:1098053868371-compute@developer.gserviceaccount.com"
```

### Permission errors

Grant storage access to Cloud Run service account:
```bash
gcloud projects add-iam-policy-binding gen-lang-client-0148980288 \
  --member="serviceAccount:1098053868371-compute@developer.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

## Next Steps

After deployment:
1. ✅ Test `/projects` endpoint
2. ✅ Verify project count matches bucket
3. ✅ Test downloading a project
4. ✅ Test activating an archived project
