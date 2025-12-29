#!/bin/bash
# User Data Script for EC2 Instance Initialization

set -e

# Update system
apt-get update
apt-get upgrade -y

# Install dependencies
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    nginx \
    curl

# Create application directory
mkdir -p /opt/researchbuddy
cd /opt/researchbuddy

# Clone repository (replace with your repo URL)
git clone https://github.com/swan28pande/ResearchBuddy.git .

# Set up Python virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Create .env file
cat > backend/.env << EOF
OPENAI_API_KEY=${openai_api_key}
TAVILY_API_KEY=${tavily_api_key}
SEMANTIC_SCHOLAR_API_KEY=${semantic_scholar_api_key}
EOF

# Create systemd service for backend
cat > /etc/systemd/system/researchbuddy-backend.service << 'EOF'
[Unit]
Description=ResearchBuddy Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/researchbuddy/backend
Environment="PATH=/opt/researchbuddy/.venv/bin"
ExecStart=/opt/researchbuddy/.venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure nginx as reverse proxy
cat > /etc/nginx/sites-available/researchbuddy << 'EOF'
server {
    listen 8000;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/researchbuddy /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Start services
systemctl daemon-reload
systemctl enable researchbuddy-backend
systemctl start researchbuddy-backend
systemctl restart nginx

echo "ResearchBuddy backend setup complete!"
