# Deploying the FastAPI Backend to Google Cloud Run

This guide shows how to containerise the FastAPI backend and deploy it on **Google Cloud Run** using Cloud Build. It covers both an automated CI/CD workflow (`cloudbuild.yaml`) and an alternative manual deployment.

> ⚠️ **Operational note**: the `/generate` pipeline writes Expo projects to disk, installs npm dependencies, and opens public tunnels via ngrok. Cloud Run provides ephemeral disk space and may scale replicas horizontally, so ensure this behaviour matches your production requirements before exposing the service publicly.

## 1. Prerequisites
- Google Cloud project with billing enabled.
- `gcloud` CLI installed and initialised (`gcloud init`).
- Artifact Registry API & Cloud Run API enabled.
- Service account with permissions:
  - `roles/artifactregistry.admin`
  - `roles/run.admin`
  - `roles/iam.serviceAccountUser`
- Secrets for runtime configuration:
  - `OPENAI_API_KEY`
  - `NGROK_AUTH_TOKEN`
  - Optional: `API_KEY` (if `REQUIRE_API_KEY=true`)

## 2. Build the container image

The repository already includes a production-ready `Dockerfile` in `backend/`. Build locally with:

```bash
cd backend
docker build -t gcr.io/PROJECT_ID/ai-expo-backend:latest .
```

> Replace `PROJECT_ID` as needed. If you prefer Artifact Registry, use `REGION-docker.pkg.dev/PROJECT_ID/REPO/ai-expo-backend:latest`.

## 3. Configure Google Cloud resources

```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com
gcloud artifacts repositories create ai-expo-backend \
  --repository-format=docker \
  --location=us-central1
```

Create secrets for runtime values (repeat per secret):

```bash
printf "YOUR_OPENAI_KEY" | gcloud secrets create OPENAI_API_KEY --data-file=-
printf "YOUR_NGROK_TOKEN" | gcloud secrets create NGROK_AUTH_TOKEN --data-file=-
```

If you require API authentication:

```bash
printf "YOUR_INTERNAL_API_KEY" | gcloud secrets create API_KEY --data-file=-
```

## 4. Deploy with Cloud Build (recommended)

1. Push your code to a Cloud Source Repository / GitHub / GitLab mirror connected to Cloud Build.
2. From the repository root run:

   ```bash
   gcloud builds submit backend \
     --config=backend/cloudbuild.yaml \
     --substitutions=_REGION=us-central1,_SERVICE_NAME=ai-expo-backend,_REPOSITORY=ai-expo-backend
   ```

   Cloud Build will:
   - Build the container image.
   - Push it to Artifact Registry.
   - Deploy to Cloud Run with the provided substitutions.

3. Attach secrets and environment variables:

   ```bash
   gcloud run services update ai-expo-backend \
     --region=us-central1 \
     --update-secrets=OPENAI_API_KEY=OPENAI_API_KEY:latest,NGROK_AUTH_TOKEN=NGROK_AUTH_TOKEN:latest \
     --set-env-vars=REQUIRE_API_KEY=true \
     --update-secrets=API_KEY=API_KEY:latest
   ```

   Adjust the `--set-env-vars` flag to match your configuration (e.g. `PROJECTS_BASE_DIR=/tmp/projects`).

## 5. Manual deployment alternative

```bash
cd backend
docker build -t us-central1-docker.pkg.dev/PROJECT_ID/ai-expo-backend/ai-expo-backend:latest .
docker push us-central1-docker.pkg.dev/PROJECT_ID/ai-expo-backend/ai-expo-backend:latest

gcloud run deploy ai-expo-backend \
  --image=us-central1-docker.pkg.dev/PROJECT_ID/ai-expo-backend/ai-expo-backend:latest \
  --region=us-central1 \
  --port=8080 \
  --allow-unauthenticated
```

Add secrets and environment variables as described in section 4.

## 6. Post-deployment checklist
- **Set concurrency**: Cloud Run defaults to 80 concurrent requests. Lower this (e.g. `--concurrency=1`) if long-running `generate` operations compete for system resources.
- **Adjust scaling limits**: Update `_MAX_INSTANCES` / `_MIN_INSTANCES` (Cloud Build) or `--max-instances` / `--min-instances` (manual) to control scaling.
- **Logging & monitoring**: Use Cloud Logging and Cloud Monitoring dashboards to observe resource usage exposed by `/metrics`.
- **Ingress restrictions**: When `require_api_key` is enabled, add `X-API-Key` header checks; otherwise restrict ingress to trusted networks.
- **Cleanup**: Ensure generated projects in `projects/` are periodically cleaned up to avoid filling the writable filesystem.

With these steps, the FastAPI backend should be reachable at the Cloud Run service URL returned by the deployment command.

