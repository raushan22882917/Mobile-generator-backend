# Ngrok Authentication Token Fix

## Issue
```
authentication failed: The authtoken you specified is properly formed, but it is invalid.
Your authtoken: 35GXfjXOtRduaWSJHG23ztdM3ID_6rhcac7qafonpV8hJrs8f
ERR_NGROK_107
```

## Root Cause
The ngrok authentication token being used is invalid. This happens when:
- Token was reset/revoked
- Token was for a team account you were removed from
- Using an old/cached token

## Solution

### Option 1: Update Cloud Run Environment Variable (Production)

1. Get a new valid token from ngrok dashboard:
   https://dashboard.ngrok.com/get-started/your-authtoken

2. Update Cloud Run service:
   ```bash
   gcloud run services update ai-expo-builder \
     --update-env-vars NGROK_AUTH_TOKEN=YOUR_NEW_TOKEN_HERE \
     --region us-central1
   ```

3. Or via Cloud Console:
   - Go to Cloud Run → ai-expo-builder
   - Click "Edit & Deploy New Revision"
   - Go to "Variables & Secrets" tab
   - Update `NGROK_AUTH_TOKEN` value
   - Deploy

### Option 2: Update Local .env File (Development)

Your current `.env` has:
```
NGROK_AUTH_TOKEN=35NlETanMCIrFlmG1q6PlNV5BPl_62CKhyNcuWcqENXT9aUvt
```

If this token is also invalid:
1. Get new token from: https://dashboard.ngrok.com/get-started/your-authtoken
2. Update `.env` file with new token
3. Restart the application

### Option 3: Verify Token is Being Read Correctly

Check if environment variable is being overridden:
```bash
# On Cloud Run, check current env vars
gcloud run services describe ai-expo-builder --region us-central1 --format="value(spec.template.spec.containers[0].env)"

# Locally, verify .env is being loaded
python -c "from config import settings; print(settings.ngrok_auth_token[:10] + '...')"
```

## Verification

After updating the token, test the tunnel creation:
```bash
# The application should start without ngrok errors
# Check logs for successful tunnel creation
```

## Note
The token in the error message (`35GXfjXOtRduaWSJHG23ztdM3ID_6rhcac7qafonpV8hJrs8f`) is different from your `.env` token, suggesting the production environment is using a different (invalid) token.
