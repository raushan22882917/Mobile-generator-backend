# Quick Fix: Cloud Storage Not Working

## The Problem
Projects are not being saved to or fetched from Google Cloud Storage.

## Root Cause
The `GOOGLE_APPLICATION_CREDENTIALS` environment variable is not set, so the application can't authenticate with Google Cloud.

---

## Quick Fix (Choose One)

### Option 1: Command Prompt (CMD)
```cmd
setup-google-credentials-permanent.cmd
```
Then **restart your terminal/IDE**.

### Option 2: PowerShell
```powershell
.\setup-google-credentials-permanent.ps1
```
Then **restart your terminal/IDE**.

### Option 3: Manual Setup
1. Right-click "This PC" → Properties → Advanced System Settings
2. Click "Environment Variables"
3. Under "User variables", click "New"
4. Variable name: `GOOGLE_APPLICATION_CREDENTIALS`
5. Variable value: `D:\Mobile-generator-backend\service-account-key.json`
6. Click OK
7. **Restart your terminal/IDE**

---

## Verify It Works

After restarting your terminal:

```cmd
python test_cloud_storage.py
```

Expected output:
```
✅ Cloud Storage is AVAILABLE
✅ Successfully accessed bucket
```

---

## What Was Fixed

1. ✅ Added `ensure_project_available()` helper to fetch projects from Cloud Storage
2. ✅ Added Cloud Storage availability checks before upload
3. ✅ Fixed credential path in `.env`
4. ✅ Created setup scripts for easy configuration
5. ✅ Updated all endpoints to fetch from Cloud Storage when needed

---

## Files Changed

- `main.py` - Added helper function and updated endpoints
- `services/streaming_generator.py` - Added Cloud Storage checks
- `.env` - Removed incorrect credentials path
- `config.py` - Made credentials optional

---

## Next Steps

1. Run the setup script
2. Restart your terminal/IDE
3. Test with `python test_cloud_storage.py`
4. Start your application: `uvicorn main:app --reload`
5. Create a test project and verify it uploads to Cloud Storage

---

## For Production (Cloud Run)

You don't need the service account key file in Cloud Run. See `GOOGLE_CLOUD_CREDENTIALS_SETUP.md` for details on using default service accounts.
