#!/usr/bin/env bash
# ==============================================================================
# Automated 24/7 Cloud Production Deployment Script for Ubuntu / Debian VPS
# Pakistan Food Business Intelligence & AI Lead Hunter Platform
# ==============================================================================

set -e

echo ">>> [1/5] Updating system packages & installing prerequisites..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv nginx curl git

APP_DIR="/opt/pakistan_food_pos_intel"

echo ">>> [2/5] Preparing application directory at $APP_DIR..."
if [ ! -d "$APP_DIR" ]; then
    sudo mkdir -p "$APP_DIR"
    sudo cp -r . "$APP_DIR"
fi

cd "$APP_DIR"
sudo chown -R $USER:$USER "$APP_DIR"

echo ">>> [3/5] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Ensure database exists
if [ ! -f "database/food_intel.db" ]; then
    echo ">>> Initializing database..."
    python database/db_manager.py
fi

echo ">>> [4/5] Creating 24/7 systemd service (auto-restart on failure & boot)..."
SERVICE_FILE="/etc/systemd/system/foodpos.service"
sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Pakistan Food Business Intelligence & POS Lead Hunter
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="PORT=5000"
Environment="APP_ENV=production"
ExecStart=$APP_DIR/venv/bin/gunicorn api.server:app --bind 127.0.0.1:5000 --workers 2 --threads 4 --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable foodpos
sudo systemctl restart foodpos

echo ">>> [5/5] Configuring Nginx Reverse Proxy..."
NGINX_CONF="/etc/nginx/sites-available/foodpos"
sudo bash -c "cat > $NGINX_CONF" <<EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 180s;
        proxy_connect_timeout 60s;
    }
}
EOF

sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "=============================================================================="
echo ">>> SUCCESS! Platform is now LIVE online 24/7 at http://$(curl -s ifconfig.me)"
echo ">>> The AI Daily Lead Hunter will automatically run at 02:00 AM PKT daily."
echo ">>> Service status can be checked via: sudo systemctl status foodpos"
echo "=============================================================================="

