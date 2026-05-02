#!/bin/bash
#
# LofiGen Pro - One-Command VPS Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/lofi-video-generator/main/install.sh | bash
#

set -e

LOFI_COLOR="\033[36m"
SUCCESS_COLOR="\033[32m"
ERROR_COLOR="\033[31m"
RESET_COLOR="\033[0m"

log() {
    echo -e "${LOFI_COLOR}[LofiGen]${RESET_COLOR} $1"
}

success() {
    echo -e "${SUCCESS_COLOR}✓${RESET_COLOR} $1"
}

error() {
    echo -e "${ERROR_COLOR}✗${RESET_COLOR} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    error "Please run as root or with sudo"
    exit 1
fi

log "🎵 LofiGen Pro Installer"
log "=========================="

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    error "Cannot detect OS"
    exit 1
fi

log "Detected OS: $OS"

# Install Docker
if ! command -v docker &> /dev/null; then
    log "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    success "Docker installed"
else
    success "Docker already installed"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    log "Installing Docker Compose..."
    DOCKER_COMPOSE_VERSION="2.23.0"
    curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    success "Docker Compose installed"
else
    success "Docker Compose already installed"
fi

# Add user to docker group
USERNAME=${SUDO_USER:-$USER}
usermod -aG docker $USERNAME
log "Added $USERNAME to docker group"

# Create installation directory
INSTALL_DIR="/opt/lofigen"
log "Creating installation directory: $INSTALL_DIR"
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Clone repository (or use local files)
if [ ! -d "$INSTALL_DIR/.git" ]; then
    log "Cloning LofiGen repository..."
    # For production, use the actual repo URL
    # git clone https://github.com/YOUR_USERNAME/lofi-video-generator.git .
    log "Please ensure lofi_gen/ directory and docker-compose.yml are in $INSTALL_DIR"
fi

# Create .env file if not exists
if [ ! -f ".env" ]; then
    log "Creating .env configuration file..."
    cat > .env << 'EOF'
# Database
DB_USER=lofi
DB_PASSWORD=lofi_secure_$(openssl rand -hex 8)
DB_NAME=lofidb

# API Keys (will be configured via web interface)
KIE_API_KEY=
PEXELS_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=
AI_PROVIDER=auto

# Security
JWT_SECRET=$(openssl rand -hex 32)
EOF
    success "Created .env file"
fi

# Create output and temp directories
mkdir -p output temp
chmod 777 output temp

# Pull and start services
log "Pulling Docker images..."
docker-compose -f docker-compose.prod.yml pull

log "Starting LofiGen services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
log "Waiting for services to start..."
sleep 10

# Initialize database
log "Initializing database..."
docker-compose -f docker-compose.prod.yml exec -T api python -c "
from lofi_gen.db.connection import engine
from lofi_gen.db.models import Base
Base.metadata.create_all(bind=engine)
print('Database initialized!')
" 2>/dev/null || log "Database will be initialized on first run"

# Install Nginx if not present
if ! command -v nginx &> /dev/null; then
    log "Installing Nginx..."
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        apt-get update
        apt-get install -y nginx
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
        yum install -y nginx
    fi
    systemctl enable nginx
    success "Nginx installed"
fi

# Create Nginx config
log "Configuring Nginx..."
cat > /etc/nginx/sites-available/lofigen << 'EOF'
server {
    listen 80;
    server_name _;  # Accept any hostname
    
    client_max_body_size 100M;
    
    # API
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts for long requests
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
    
    # Web Interface
    location /web/ {
        proxy_pass http://localhost:8501/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Static downloads
    location /downloads/ {
        alias /opt/lofigen/output/;
        autoindex on;
        add_header Content-Disposition "attachment";
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/lofigen /etc/nginx/sites-enabled/lofigen
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

success "Nginx configured"

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

# Print success message
echo ""
echo -e "${SUCCESS_COLOR}🎉 LofiGen Pro installed successfully!${RESET_COLOR}"
echo ""
echo "📍 Access URLs:"
echo "   API Docs:    http://$SERVER_IP/docs"
echo "   Web UI:      http://$SERVER_IP/web/"
echo "   Health:      http://$SERVER_IP/health"
echo ""
echo "⚙️  Next Steps:"
echo "   1. Open http://$SERVER_IP/web/setup"
echo "   2. Configure your API keys (Kie.ai, Pexels)"
echo "   3. Create your first admin user"
echo "   4. Start generating videos!"
echo ""
echo "🔧 Management Commands:"
echo "   View logs:    docker-compose -f $INSTALL_DIR/docker-compose.prod.yml logs -f"
echo "   Restart:      docker-compose -f $INSTALL_DIR/docker-compose.prod.yml restart"
echo "   Update:       docker-compose -f $INSTALL_DIR/docker-compose.prod.yml pull && docker-compose up -d"
echo ""
echo "📁 Installation Directory: $INSTALL_DIR"
echo "📄 Configuration File:     $INSTALL_DIR/.env"
echo ""
