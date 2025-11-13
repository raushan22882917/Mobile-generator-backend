@echo off
REM Setup Google Cloud Secrets for Cloud Run deployment
REM Reads API keys from .env file automatically
REM
REM Usage: setup-secrets.cmd

set PROJECT_ID=gen-lang-client-0148980288

echo Setting up secrets for project: %PROJECT_ID%
echo Reading credentials from .env file...
echo.

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found
    exit /b 1
)

REM Load environment variables from .env file
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    set "line=%%a"
    if not "!line:~0,1!"=="#" (
        set "%%a=%%b"
    )
)

REM Check if environment variables are loaded
if "%OPENAI_API_KEY%"=="" (
    echo ERROR: OPENAI_API_KEY not found in .env file
    exit /b 1
)

if "%NGROK_AUTH_TOKEN%"=="" (
    echo ERROR: NGROK_AUTH_TOKEN not found in .env file
    exit /b 1
)

if "%GEMINI_API_KEY%"=="" (
    echo ERROR: GEMINI_API_KEY not found in .env file
    exit /b 1
)

echo [OK] Credentials loaded from .env
echo.

REM Create secrets (if they don't exist)
echo Creating secrets...
echo.

REM OpenAI API Key
echo Creating/updating openai-api-key...
echo %OPENAI_API_KEY% | gcloud secrets create openai-api-key --data-file=- --project=%PROJECT_ID% --replication-policy=automatic 2>nul
if errorlevel 1 (
    echo %OPENAI_API_KEY% | gcloud secrets versions add openai-api-key --data-file=- --project=%PROJECT_ID%
)
echo [OK] OpenAI API Key secret created/updated
echo.

REM Ngrok Auth Token
echo Creating/updating ngrok-auth-token...
echo %NGROK_AUTH_TOKEN% | gcloud secrets create ngrok-auth-token --data-file=- --project=%PROJECT_ID% --replication-policy=automatic 2>nul
if errorlevel 1 (
    echo %NGROK_AUTH_TOKEN% | gcloud secrets versions add ngrok-auth-token --data-file=- --project=%PROJECT_ID%
)
echo [OK] Ngrok Auth Token secret created/updated
echo.

REM Gemini API Key
echo Creating/updating gemini-api-key...
echo %GEMINI_API_KEY% | gcloud secrets create gemini-api-key --data-file=- --project=%PROJECT_ID% --replication-policy=automatic 2>nul
if errorlevel 1 (
    echo %GEMINI_API_KEY% | gcloud secrets versions add gemini-api-key --data-file=- --project=%PROJECT_ID%
)
echo [OK] Gemini API Key secret created/updated
echo.

echo All secrets created successfully!
echo.
echo Now you can deploy with: gcloud builds submit --config cloudbuild.yaml
pause
