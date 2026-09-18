#!/usr/bin/env bash
# NAZORAT Production Server Initial Provisioning Script
# Target OS: Ubuntu 22.04 / 24.04 LTS
# Usage: sudo ./ops/scripts/setup-server.sh

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "[-] ERROR: This script must be run as root (sudo)." >&2
  exit 1
fi

echo "=========================================="
echo "NAZORAT Production Server Provisioning"
echo "=========================================="

# 1. Set Timezone to Asia/Tashkent (Mandatory Clinical Domain Rule)
echo "[1/8] Setting timezone to Asia/Tashkent..."
timedatectl set-timezone Asia/Tashkent
timedatectl set-ntp on

# 2. Update package repositories
echo "[2/8] Updating package lists and upgrading base packages..."
apt-get update && apt-get upgrade -y
apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    ufw \
    fail2ban \
    htop \
    iotop \
    rsync \
    git \
    tar \
    gzip

# 3. Configure Swap (2GB) to prevent Out-Of-Memory container kills
if [ ! -f /swapfile ]; then
    echo "[3/8] Setting up 2GB swap file..."
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    sysctl vm.swappiness=10
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
else
    echo "[3/8] Swap file already exists, skipping."
fi

# 4. Install Docker Engine & Docker Compose plugin
if ! command -v docker >/dev/null 2>&1; then
    echo "[4/8] Installing Docker Engine..."
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable docker
    systemctl start docker
else
    echo "[4/8] Docker already installed."
fi

# 5. Configure Kernel Sysctl parameters for production
echo "[5/8] Tuning network sysctl parameters..."
cat << 'EOF' > /etc/sysctl.d/99-nazorat-network.conf
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
EOF
sysctl --system > /dev/null

# 6. Configure UFW Firewall
echo "[6/8] Configuring UFW Firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment "SSH"
ufw allow 80/tcp comment "HTTP (Certbot & Nginx)"
ufw allow 443/tcp comment "HTTPS (Nginx)"
ufw --force enable

# 7. Configure Fail2ban
echo "[7/8] Configuring Fail2ban for SSH..."
systemctl enable fail2ban
systemctl restart fail2ban

# 8. Create system directories
echo "[8/8] Creating deployment directories..."
mkdir -p /opt/nazorat /opt/nazorat/ops/backups

echo "=========================================="
echo "[✓] Server provisioning completed successfully!"
echo "Server Time: $(date)"
echo "Docker Version: $(docker --version)"
echo "Compose Version: $(docker compose version)"
echo "=========================================="
