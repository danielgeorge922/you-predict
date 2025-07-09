# YouTube Predictor Setup Script for PowerShell
# Run this as Administrator

Write-Host "===============================================" -ForegroundColor Green
Write-Host "YouTube Predictor - PowerShell Setup" -ForegroundColor Green  
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

# Set variables
$PROJECT_ID = "you-predict-462918"
$SERVICE_ACCOUNT = "youtube-predictor-robot"
$SERVICE_ACCOUNT_EMAIL = "$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com"
$KEY_FILE = "$env:USERPROFILE\.gcp\youtube-predictor-key.json"
$ENV_FILE = "$env:USERPROFILE\.gcp\youtube-predictor.env"

Write-Host "Project ID: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "Service Account: $SERVICE_ACCOUNT_EMAIL" -ForegroundColor Yellow
Write-Host ""

# Step 1: Verify gcloud is working
Write-Host "STEP 1: Checking gcloud installation..." -ForegroundColor Cyan
try {
    $version = gcloud --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ gcloud is working" -ForegroundColor Green
    } else {
        throw "gcloud not found"
    }
} catch {
    Write-Host "❌ gcloud not found. Please install Google Cloud CLI first." -ForegroundColor Red
    exit 1
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

# Step 3: Login (fix permission issues)
Write-Host "STEP 3: Authenticating..." -ForegroundColor Cyan
Write-Host "This will open a browser window for login..." -ForegroundColor Yellow
gcloud auth login --no-launch-browser 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Trying alternative login method..." -ForegroundColor Yellow
    gcloud auth login
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Authentication successful" -ForegroundColor Green
} else {
    Write-Host "❌ Authentication failed" -ForegroundColor Red
    Write-Host "Please run this manually: gcloud auth login" -ForegroundColor Yellow
}

# Step 4: Enable APIs
Write-Host "STEP 4: Enabling required APIs..." -ForegroundColor Cyan
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
    gcloud services enable $api 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $api enabled" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ $api may already be enabled" -ForegroundColor Yellow
    }
}

# Step 5: Create service account (if not exists)
Write-Host "STEP 5: Creating service account..." -ForegroundColor Cyan
gcloud iam service-accounts create $SERVICE_ACCOUNT --display-name="YouTube Predictor Robot" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Service account created" -ForegroundColor Green
} else {
    Write-Host "⚠️ Service account may already exist" -ForegroundColor Yellow
}

# Step 6: Grant permissions (fix the typo from your earlier command)
Write-Host "STEP 6: Granting permissions..." -ForegroundColor Cyan
$roles = @(
    "roles/compute.instanceAdmin",
    "roles/secretmanager.secretAccessor", 
    "roles/cloudsql.client",
    "roles/cloudfunctions.invoker"
)

foreach ($role in $roles) {
    Write-Host "  Granting $role..." -ForegroundColor Yellow
    gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" --role="$role" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $role granted" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ $role may already be granted" -ForegroundColor Yellow
    }
}

# Step 7: Create .gcp directory and key file
Write-Host "STEP 7: Creating authentication key..." -ForegroundColor Cyan
$gcpDir = "$env:USERPROFILE\.gcp"
if (!(Test-Path $gcpDir)) {
    New-Item -ItemType Directory -Path $gcpDir -Force | Out-Null
    Write-Host "✅ Created .gcp directory" -ForegroundColor Green
}

# Check if key file already exists
if (Test-Path $KEY_FILE) {
    Write-Host "⚠️ Key file already exists at $KEY_FILE" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to create a new key? (y/n)"
    if ($overwrite -eq "y" -or $overwrite -eq "Y") {
        Remove-Item $KEY_FILE -Force
        gcloud iam service-accounts keys create $KEY_FILE --iam-account=$SERVICE_ACCOUNT_EMAIL
    }
} else {
    gcloud iam service-accounts keys create $KEY_FILE --iam-account=$SERVICE_ACCOUNT_EMAIL
}

if (Test-Path $KEY_FILE) {
    Write-Host "✅ Authentication key created at $KEY_FILE" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create authentication key" -ForegroundColor Red
}

# Step 8: Create environment file
Write-Host "STEP 8: Creating environment file..." -ForegroundColor Cyan
@"
# YouTube Predictor Environment Variables
`$env:GOOGLE_CLOUD_PROJECT = "$PROJECT_ID"
`$env:GOOGLE_APPLICATION_CREDENTIALS = "$KEY_FILE"
`$env:GCLOUD_PROJECT = "$PROJECT_ID"
"@ | Out-File -FilePath $ENV_FILE -Encoding UTF8

Write-Host "✅ Environment file created at $ENV_FILE" -ForegroundColor Green

# Step 9: Test setup
Write-Host "STEP 9: Testing setup..." -ForegroundColor Cyan
$env:GOOGLE_APPLICATION_CREDENTIALS = $KEY_FILE

# Test project access
$currentProject = gcloud config get-value project 2>$null
if ($currentProject -eq $PROJECT_ID) {
    Write-Host "✅ Project access working" -ForegroundColor Green
} else {
    Write-Host "❌ Project access failed" -ForegroundColor Red
}

# Test service account
$serviceAccounts = gcloud iam service-accounts list --format="value(email)" 2>$null
if ($serviceAccounts -like "*$SERVICE_ACCOUNT_EMAIL*") {
    Write-Host "✅ Service account exists" -ForegroundColor Green
} else {
    Write-Host "❌ Service account not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "✅ Project: $PROJECT_ID" -ForegroundColor Green
Write-Host "✅ Service Account: $SERVICE_ACCOUNT_EMAIL" -ForegroundColor Green  
Write-Host "✅ Key File: $KEY_FILE" -ForegroundColor Green
Write-Host "✅ Environment: $ENV_FILE" -ForegroundColor Green
Write-Host ""
Write-Host "💡 To use this setup in future sessions, run:" -ForegroundColor Yellow
Write-Host "   . $ENV_FILE" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Get your YouTube API key" -ForegroundColor White
Write-Host "2. Store it securely" -ForegroundColor White
Write-Host "3. Create your free VM" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = Read-Host