#!/usr/bin/env bash
# WMAX Enterprise Server Provisioning Script
# Target: Ubuntu 24.04 LTS
# Role: Principal DevOps & Security Engineer
# Usage: sudo ./scripts/setup_server.sh

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "[-] ERROR: This provisioning script must be run as root (sudo)." >&2
  exit 1
fi

DEPLOY_USER="deploy"
TIMEZONE="Asia/Tashkent"

echo "========================================================"
echo "  WMAX Enterprise Server Provisioning (Ubuntu 24.04)"
echo "========================================================"

# 1. System Timezone & Locale
echo "[1/9] Configuring Timezone (${TIMEZONE}) & Locales..."
timedatectl set-timezone "${TIMEZONE}"
timedatectl set-ntp on
locale-gen en_US.UTF-8 uz_UZ.UTF-8
update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

# 2. Base System Upgrade & Utilities
echo "[2/9] Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update && apt-get upgrade -y
apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    ufw \
    fail2ban \
    logrotate \
    restic \
    htop \
    iotop \
    rsync \
    git \
    tar \
    gzip \
    unattended-upgrades

# 3. Swap Space Setup (Prevents OOM container terminations)
if [ ! -f /swapfile ]; then
    echo "[3/9] Creating 4GB Swap file..."
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    sysctl vm.swappiness=10
    echo 'vm.swappiness=10' >> /etc/sysctl.d/99-swap.conf
else
    echo "[3/9] Swap already present."
fi

# 4. Create Non-Root Deploy User
echo "[4/9] Setting up non-root deploy user: ${DEPLOY_USER}..."
if ! id -u "${DEPLOY_USER}" >/dev/null 2>&1; then
    useradd -m -s /bin/bash -G sudo,docker "${DEPLOY_USER}" || useradd -m -s /bin/bash -G sudo "${DEPLOY_USER}"
    echo "${DEPLOY_USER} ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/90-${DEPLOY_USER}"
    chmod 0440 "/etc/sudoers.d/90-${DEPLOY_USER}"

    mkdir -p "/home/${DEPLOY_USER}/.ssh"
    if [ -f /root/.ssh/authorized_keys ]; then
        cp /root/.ssh/authorized_keys "/home/${DEPLOY_USER}/.ssh/"
    fi
    chmod 700 "/home/${DEPLOY_USER}/.ssh"
    chmod 600 "/home/${DEPLOY_USER}/.ssh/authorized_keys" 2>/dev/null || true
    chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "/home/${DEPLOY_USER}/.ssh"
fi

# 5. Install Official Docker CE & Compose Plugin
echo "[5/9] Installing Docker Engine & Docker Compose..."
if ! command -v docker >/dev/null 2>&1; then
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
    usermod -aG docker "${DEPLOY_USER}"
fi

# 6. Kernel Network & Security Hardening
echo "[6/9] Applying sysctl kernel hardening..."
cat << 'EOF' > /etc/sysctl.d/99-wmax-security.conf
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
fs.file-max = 2097152
EOF
sysctl --system > /dev/null

# 7. UFW Firewall Configuration
echo "[7/9] Configuring UFW Firewall (Ports 22, 80, 443)..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment "SSH"
ufw allow 80/tcp comment "HTTP / ACME"
ufw allow 443/tcp comment "HTTPS / TLS"
ufw --force enable

# 8. Fail2ban & SSH Hardening
echo "[8/9] Hardening SSH & Fail2ban..."
cat << 'EOF' > /etc/fail2ban/jail.local
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true
port = 22
EOF
systemctl enable fail2ban
systemctl restart fail2ban

# Harden sshd_config
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
systemctl restart ssh || systemctl restart sshd

# 9. Docker Logrotate Setup
echo "[9/9] Configuring Docker container logrotate..."
cat << 'EOF' > /etc/logrotate.d/docker-containers
/var/lib/docker/containers/*/*-json.log {
    rotate 5
    daily
    compress
    missingok
    delaycompress
    copytruncate
    maxsize 50M
}
EOF

mkdir -p /opt/wmax/backups /opt/wmax/logs
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" /opt/wmax

echo "========================================================"
echo "[✓] Enterprise Provisioning Complete!"
echo "    - Timezone: $(date)"
echo "    - Deploy User: ${DEPLOY_USER} (Key-only sudo access)"
echo "    - Firewall: Active (22, 80, 443)"
echo "    - Docker: $(docker --version)"
echo "========================================================"
