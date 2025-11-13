# Cloud Storage Only Architecture

## Overview

The backend now operates in a **cloud-only** mode where all projects are stored exclusively in Google Cloud Storage. Local disk is used only temporarily during generation.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Project Generation Flow                   │
└─────────────────────────────────────────────────────────────┘

1. User Request
   └─> Create project in /tmp/projects/{project_id}/
   
2. Generate Code
   └─> Write files to /tmp/projects/{project_id}/
   
3. Install Dependencies
   └─> npm install in /tmp/projects/{project_id}/
   
4. Start Server & Create Tunnel
   └─> Expo server runs from /tmp/projects/{project_id}/
   
5. Upload to Cloud Storage
   └─> ZIP and upload to gs://bucket/projects/{project_id}.zip
   
6. Clean Up Local Files
   └─> Delete /tmp/projects/{project_id}/
   
7. Return Success
   └─> Project accessible via Cloud Storage
```

## File Access Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    File Access Flow                          │
└─────────────────────────────────────────────────────────────┘

1. User requests /files/{project_id}
   
2. Check if project exists locally
   └─> NO: Download from Cloud Storage
       └─> Extract to /tmp/projects/{project_id}/
       └─> Create project object in memory
   
3. Return file tree
   
4. (Optional) Clean up after serving
```

## Benefits

### 1. **No Local Storage Waste**
- Projects are deleted immediately after upload
- `/tmp` directory stays clean
- No risk of disk full errors

### 2. **Perfect for Cloud Run**
- Cloud Run containers are ephemeral
- `/tmp` is cleared on restart
- Projects persist in Cloud Storage indefinitely

### 3. **Single Source of Truth**
- All projects in one place: Cloud Storage bucket
- No sync issues between local and cloud
- Easy backup and disaster recovery

### 4. **Cost Efficient**
- No need for persistent disks
- Pay only for Cloud Storage (cheap)
- Cloud Run can scale to zero

### 5. **Scalable**
- Multiple instances can access same projects
- No shared filesystem needed
- Horizontal scaling works perfectly

## Configuration

### Environment Variables

```env
# Cloud Storage (required)
GOOGLE_CLOUD_PROJECT=gen-lang-client-0148980288
GOOGLE_CLOUD_BUCKET=gen-lang-client-0148980288-ai-expo-builder-archives
GOOGLE_APPLICATION_CREDENTIALS=backend/service-account-key.json

# Temporary directory (ephemeral)
PROJECTS_BASE_DIR=/tmp/projects
```

### Cloud Run Deployment

The `cloudbuild.yaml` automatically sets:
```yaml
--set-env-vars=PROJECTS_BASE_DIR=/tmp/projects,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_BUCKET=...
```

## Storage Locations

### During Generation
- **Local**: `/tmp/projects/{project_id}/`
- **Duration**: Only during generation (5-10 minutes)
- **Cleaned**: Immediately after upload

### After Generation
- **Cloud Storage**: `gs://bucket/projects/{project_id}.zip`
- **Duration**: Indefinite (until manually deleted)
- **Access**: Download on-demand when needed

## API Endpoints

### Generate Project
```
POST /generate
POST /api/v1/streaming-generate
POST /api/v1/fast-generate
```
- Creates project in `/tmp`
- Uploads to Cloud Storage
- Deletes local files
- Returns project_id and preview_url

### Access Files
```
GET /files/{project_id}
```
- Checks local cache first
- Downloads from Cloud Storage if not found
- Returns file tree

### Download Project
```
GET /api/download/{project_id}
```
- Streams ZIP directly from Cloud Storage
- No local storage needed

## Monitoring

### Check Cloud Storage Usage
```bash
gsutil du -sh gs://gen-lang-client-0148980288-ai-expo-builder-archives/projects/
```

### List All Projects
```bash
gsutil ls gs://gen-lang-client-0148980288-ai-expo-builder-archives/projects/
```

### Check Local Disk Usage (should be minimal)
```bash
du -sh /tmp/projects/
```

## Cleanup

### Automatic Cleanup
- Local files deleted after upload ✅
- No manual cleanup needed ✅

### Manual Cleanup (if needed)
```bash
# Clean up old projects from Cloud Storage
gsutil rm gs://gen-lang-client-0148980288-ai-expo-builder-archives/projects/old-project-id.zip
```

## Troubleshooting

### Project Not Found
- Check if project exists in Cloud Storage:
  ```bash
  gsutil ls gs://bucket/projects/{project_id}.zip
  ```

### Upload Failed
- Check Cloud Storage permissions
- Verify service account has `storage.objects.create` permission

### Download Failed
- Check if ZIP file exists in bucket
- Verify service account has `storage.objects.get` permission

## Migration from Local Storage

If you have existing projects in local storage:

```bash
# Upload existing projects to Cloud Storage
for dir in ./projects/*/; do
  project_id=$(basename "$dir")
  zip -r "/tmp/${project_id}.zip" "$dir"
  gsutil cp "/tmp/${project_id}.zip" "gs://bucket/projects/${project_id}.zip"
done
```

## Summary

✅ **All projects stored in Cloud Storage**  
✅ **Local disk used only temporarily**  
✅ **Automatic cleanup after upload**  
✅ **Perfect for Cloud Run deployment**  
✅ **Scalable and cost-efficient**  
✅ **Single source of truth**
