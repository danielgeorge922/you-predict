# Fixed YouTube Predictor Setup Script
# This version uses your personal account for setup

Write-Host "===============================================" -ForegroundColor Green
Write-Host "YouTube Predictor - Fixed Setup" -ForegroundColor Green  
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

# Set variables
$PROJECT_ID = "you-predict-462918"
$SERVICE_ACCOUNT = "youtube-predictor-robot"
$SERVICE_ACCOUNT_EMAIL = "$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com"
$KEY_FILE = "$env:USERPROFILE\.gcp\youtube-predictor-key.json"
$ENV_FILE = "$env:USERPROFILE\.gcp\youtube-predictor.env"

Write-Host "Project ID: $PROJECT_ID" -ForegroundColor Yellow
Write-Host ""

# Step 1: Make sure we're using personal account
Write-Host "STEP 1: Ensuring we're using your personal account..." -ForegroundColor Cyan
$currentAccount = gcloud config get-value account 2>$null
Write-Host "Current account: $currentAccount" -ForegroundColor Yellow

if ($currentAccount -like "*$SERVICE_ACCOUNT*") {
    Write-Host "⚠️ Currently using service account. Switching to personal account..." -ForegroundColor Yellow
    Write-Host "Please complete the login in your browser..." -ForegroundColor Yellow
    gcloud auth login
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Switched to personal account" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to switch accounts" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Using personal account" -ForegroundColor Green
}

# Step 2: Set project
Write-Host "STEP 2: Setting project..." -ForegroundColor Cyan
gcloud config set project $PROJECT_ID
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Project set to $PROJECT_ID" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to set project" -ForegroundColor Red
    exit 1
}

# Step 3: Enable essential APIs first
Write-Host "STEP 3: Enabling essential APIs..." -ForegroundColor Cyan
$essentialApis = @(
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com", 
    "serviceusage.googleapis.com"
)

foreach ($api in $essentialApis) {
    Write-Host "  Enabling $api..." -ForegroundColor Yellow
    gcloud services enable $api
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $api enabled" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Failed to enable $api" -ForegroundColor Red
    }
}

# Step 4: Enable other required APIs
Write-Host "STEP 4: Enabling other required APIs..." -ForegroundColor Cyan
$apis = @(
    "compute.googleapis.com",
    "cloudfunctions.googleapis.com", 
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudscheduler.googleapis.com"
)

foreach ($api in $apis) {
    Write-Host "  Enabling $api..." -ForegroundColor Yellow
    gcloud services enable $api
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $api enabled" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ $api may already be enabled or failed" -ForegroundColor Yellow
    }
}

# Step 5: Create service account
Write-Host "STEP 5: Creating service account..." -ForegroundColor Cyan
$existingAccount = gcloud iam service-accounts list --filter="email:$SERVICE_ACCOUNT_EMAIL" --format="value(email)" 2>$null
if ($existingAccount -eq $SERVICE_ACCOUNT_EMAIL) {
    Write-Host "✅ Service account already exists" -ForegroundColor Green
} else {
    gcloud iam service-accounts create $SERVICE_ACCOUNT --display-name="YouTube Predictor Robot"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Service account created" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create service account" -ForegroundColor Red
        exit 1
    }
}

# Step 6: Grant permissions
Write-Host "STEP 6: Granting permissions..." -ForegroundColor Cyan
$roles = @(
    "roles/compute.instanceAdmin",
    "roles/secretmanager.secretAccessor", 
    "roles/cloudsql.client",
    "roles/cloudfunctions.invoker"
)

foreach ($role in $roles) {
    Write-Host "  Granting $role..." -ForegroundColor Yellow
    gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" --role="$role" --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $role granted" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ $role may already be granted" -ForegroundColor Yellow
    }
}

# Step 7: Create .gcp directory
Write-Host "STEP 7: Setting up directories..." -ForegroundColor Cyan
$gcpDir = "$env:USERPROFILE\.gcp"
if (!(Test-Path $gcpDir)) {
    New-Item -ItemType Directory -Path $gcpDir -Force | Out-Null
    Write-Host "✅ Created .gcp directory" -ForegroundColor Green
} else {
    Write-Host "✅ .gcp directory exists" -ForegroundColor Green
}

# Step 8: Create authentication key
Write-Host "STEP 8: Creating authentication key..." -ForegroundColor Cyan
if (Test-Path $KEY_FILE) {
    Write-Host "⚠️ Key file already exists. Using existing key." -ForegroundColor Yellow
} else {
    gcloud iam service-accounts keys create $KEY_FILE --iam-account=$SERVICE_ACCOUNT_EMAIL
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Authentication key created" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create authentication key" -ForegroundColor Red
        exit 1
    }
}

# Step 9: Create environment file
Write-Host "STEP 9: Creating environment file..." -ForegroundColor Cyan
@"
# YouTube Predictor Environment Variables - Load with: . "$ENV_FILE"
`$env:GOOGLE_CLOUD_PROJECT = "$PROJECT_ID"
`$env:GOOGLE_APPLICATION_CREDENTIALS = "$KEY_FILE"
`$env:GCLOUD_PROJECT = "$PROJECT_ID"

# Helper function to check if variables are loaded
function Test-YouTubeEnv {
    if (`$env:GOOGLE_CLOUD_PROJECT -eq "$PROJECT_ID") {
        Write-Host "✅ Environment loaded correctly" -ForegroundColor Green
        Write-Host "   Project: `$env:GOOGLE_CLOUD_PROJECT" -ForegroundColor Yellow
        Write-Host "   Credentials: `$env:GOOGLE_APPLICATION_CREDENTIALS" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Environment not loaded. Run: . $ENV_FILE" -ForegroundColor Red
    }
}
"@ | Out-File -FilePath $ENV_FILE -Encoding UTF8

Write-Host "✅ Environment file created" -ForegroundColor Green

# Step 10: Final verification
Write-Host "STEP 10: Final verification..." -ForegroundColor Cyan

# Check project
$currentProject = gcloud config get-value project 2>$null
if ($currentProject -eq $PROJECT_ID) {
    Write-Host "✅ Project correctly set" -ForegroundColor Green
} else {
    Write-Host "❌ Project not set correctly" -ForegroundColor Red
}

# Check service account exists
$serviceAccountExists = gcloud iam service-accounts list --filter="email:$SERVICE_ACCOUNT_EMAIL" --format="value(email)" 2>$null
if ($serviceAccountExists -eq $SERVICE_ACCOUNT_EMAIL) {
    Write-Host "✅ Service account verified" -ForegroundColor Green
} else {
    Write-Host "❌ Service account not found" -ForegroundColor Red
}

# Check key file
if (Test-Path $KEY_FILE) {
    Write-Host "✅ Key file exists" -ForegroundColor Green
} else {
    Write-Host "❌ Key file missing" -ForegroundColor Red
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Summary:" -ForegroundColor Yellow
Write-Host "✅ Project: $PROJECT_ID" -ForegroundColor Green
Write-Host "✅ Service Account: $SERVICE_ACCOUNT_EMAIL" -ForegroundColor Green  
Write-Host "✅ Key File: $KEY_FILE" -ForegroundColor Green
Write-Host "✅ Environment: $ENV_FILE" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Next time you open PowerShell, load the environment with:" -ForegroundColor Yellow
Write-Host "   . `"$ENV_FILE`"" -ForegroundColor White
Write-Host "   Test-YouTubeEnv" -ForegroundColor White
Write-Host ""
Write-Host "🚀 NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Get YouTube API key from Google Console" -ForegroundColor White
Write-Host "2. Store it securely in Secret Manager" -ForegroundColor White
Write-Host "3. Create your free VM" -ForegroundColor White
Write-Host ""
Write-Host "Press Enter to continue..." -ForegroundColor Yellow
Read-Host