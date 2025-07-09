@echo off
REM Enable Required APIs for YouTube Predictor
echo ===============================================
echo Enabling Required Google Cloud APIs
echo ===============================================
echo.
echo Project: you-predict-462918
echo.

REM Enable APIs one by one with progress
echo [1/7] Enabling Compute Engine API (for free VM)...
gcloud services enable compute.googleapis.com
if %ERRORLEVEL% EQU 0 (echo ✅ Compute Engine API enabled) else (echo ❌ Failed)
echo.

echo [2/7] Enabling Cloud Functions API (for serverless functions)...
gcloud services enable cloudfunctions.googleapis.com
if %ERRORLEVEL% EQU 0 (echo ✅ Cloud Functions API enabled) else (echo ❌ Failed)
echo.

echo [3/7] Enabling Cloud Run API (for our web API)...
gcloud services enable run.googleapis.com
if %ERRORLEVEL% EQU 0 (echo ✅ Cloud Run API enabled) else (echo ❌ Failed)
echo.

echo [4/7] Enabling Secret Manager API (for storing API keys)...
gcloud services enable secretmanager.googleapis.com
if %ERRORLEVEL% EQU 0 (echo ✅ Secret Manager API enabled) else (echo ❌ Failed)
echo.

echo [5/7] Enabling Cloud Build API (for building code)...
gcloud services enable cloudbuild.googleapis.com
if %ERRORLEVEL% EQU 0 (echo ✅ Cloud Build API enabled) else (echo ❌ Failed)
echo.

echo [6/7] Enabling Cloud Scheduler API (for scheduling tasks)...
gcloud services enable cloudscheduler.googleapis.com
if %ERRORLEVEL% EQU 0 (echo ✅ Cloud Scheduler API enabled) else (echo ❌ Failed)
echo.

echo [7/7] Enabling Cloud Logging API (for monitoring)...
gcloud services enable logging.googleapis.com
if %ERRORLEVEL% EQU 0 (echo ✅ Cloud Logging API enabled) else (echo ❌ Failed)
echo.

echo ===============================================
echo API Enablement Complete!
echo ===============================================
echo.
echo ✅ All required APIs are now enabled
echo 💰 Cost: $0.00 (API enablement is free)
echo.
echo Next step: Create service account
pause