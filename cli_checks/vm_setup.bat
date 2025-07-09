# Create a startup script for the VM
@'
#!/bin/bash
# VM Startup Script for YouTube Predictor

echo "🚀 YouTube Predictor VM Setup Starting..."
exec > >(tee -a /var/log/startup-script.log)
exec 2>&1

# Update system
echo "📦 Updating system..."
apt-get update
apt-get upgrade -y

# Install required software
echo "📦 Installing software..."
apt-get install -y python3 python3-pip python3-venv postgresql postgresql-contrib redis-server git curl htop nano

# Install Google Cloud SDK
echo "📦 Installing Google Cloud SDK..."
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
apt-get update
apt-get install -y google-cloud-cli

# Get project ID and secrets
echo "🔐 Getting configuration..."
PROJECT_ID=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/project/project-id)
DB_PASSWORD=$(gcloud secrets versions access latest --secret="db-password" --project="$PROJECT_ID")
DB_USER=$(gcloud secrets versions access latest --secret="db-username" --project="$PROJECT_ID")
DB_NAME=$(gcloud secrets versions access latest --secret="db-name" --project="$PROJECT_ID")

# Configure PostgreSQL
echo "🗄️ Setting up PostgreSQL..."
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '$DB_PASSWORD';"
sudo -u postgres createdb $DB_NAME
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"

# Configure PostgreSQL for external connections
PG_VERSION=$(ls /etc/postgresql/)
echo "listen_addresses = '*'" >> /etc/postgresql/$PG_VERSION/main/postgresql.conf
echo "host all all 0.0.0.0/0 md5" >> /etc/postgresql/$PG_VERSION/main/pg_hba.conf
systemctl restart postgresql
systemctl enable postgresql

# Configure Redis
echo "📦 Setting up Redis..."
sed -i 's/bind 127.0.0.1/bind 0.0.0.0/' /etc/redis/redis.conf
systemctl restart redis
systemctl enable redis

# Create application directory
echo "📁 Setting up application..."
mkdir -p /opt/youtube-predictor
cd /opt/youtube-predictor
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy psycopg2-binary redis structlog pydantic google-api-python-client google-cloud-secret-manager schedule requests

# Create environment file
cat > /opt/youtube-predictor/.env << EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
REDIS_URL=redis://localhost:6379/0
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
ENVIRONMENT=production
EOF

echo "✅ VM setup completed successfully!"
echo "📊 Services running: PostgreSQL (5432), Redis (6379)"
'@ | Out-File -FilePath "vm-startup.sh" -Encoding UTF8