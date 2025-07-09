@echo off
echo ===============================================
echo YouTube Predictor - Setup Check
echo ===============================================
echo.

echo Checking if gcloud is installed...
gcloud --version
if %ERRORLEVEL% NEQ 0 (
    echo ❌ gcloud not found
    echo Please install Google Cloud CLI first
    pause
    exit /b 1
) else (
    echo ✅ gcloud is working
)

echo.
echo Checking current project...
gcloud config get-value project
if %ERRORLEVEL% NEQ 0 (
    echo ❌ No project configured
    pause
    exit /b 1
) else (
    echo ✅ Project is configured
)

echo.
echo Checking authentication...
gcloud auth list --filter=status:ACTIVE --format="value(account)"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Not authenticated
    echo Run: gcloud auth login
    pause
    exit /b 1
) else (
    echo ✅ Authenticated
)

echo.
echo ===============================================
echo BASIC SETUP CHECK COMPLETE!
echo ===============================================
echo If you see all green checkmarks above, you're ready to continue.
echo If not, we need to fix the issues first.
echo.
pause