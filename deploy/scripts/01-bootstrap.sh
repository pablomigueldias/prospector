#!/usr/bin/env bash
# =============================================================================
# 01-bootstrap.sh — provisionamento inicial do VPS (CX32 / Ubuntu 24.04)
# Roda UMA vez, como root, no primeiro acesso ao servidor recém-criado.
#
#   ssh root@SEU_IP
#   bash 01-bootstrap.sh
#
# O que faz (idempotente — pode rodar de novo sem quebrar):
#   - cria usuário 'deploy' com sudo e acesso docker, herdando sua chave SSH
#   - endurece o SSH (sem login root, sem senha — só chave)
#   - firewall ufw (22, 80, 443) + fail2ban
#   - swap de 4GB (ajuda nos builds do Next.js)
#   - timezone America/Sao_Paulo + patches de segurança automáticos
#   - instala Docker + plugin compose
#
# IMPORTANTE: antes de fechar esta sessão root, ABRA OUTRO terminal e teste:
#   ssh deploy@SEU_IP
# Se logar, beleza. Se não, NÃO feche o root (você se trancaria pra fora).
# =============================================================================
set -euo pipefail

DEPLOY_USER="deploy"

echo ">> Atualizando o sistema..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y

echo ">> Timezone..."
timedatectl set-timezone America/Sao_Paulo || true

echo ">> Pacotes base..."
apt-get install -y ca-certificates curl gnupg ufw fail2ban unattended-upgrades

echo ">> Swap de 4GB..."
if [ ! -f /swapfile ]; then
  fallocate -l 4G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo 'vm.swappiness=10' > /etc/sysctl.d/99-swappiness.conf
  sysctl -p /etc/sysctl.d/99-swappiness.conf || true
else
  echo "   swap já existe, pulando."
fi

echo ">> Usuário '${DEPLOY_USER}'..."
if ! id "${DEPLOY_USER}" &>/dev/null; then
  adduser --disabled-password --gecos "" "${DEPLOY_USER}"
fi
usermod -aG sudo "${DEPLOY_USER}"
# sudo sem senha pro deploy (conforto pra automação; remova se preferir exigir senha)
echo "${DEPLOY_USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-${DEPLOY_USER}
chmod 440 /etc/sudoers.d/90-${DEPLOY_USER}

echo ">> Copiando sua chave SSH (do root) pro ${DEPLOY_USER}..."
mkdir -p /home/${DEPLOY_USER}/.ssh
if [ -f /root/.ssh/authorized_keys ]; then
  cp /root/.ssh/authorized_keys /home/${DEPLOY_USER}/.ssh/authorized_keys
fi
chmod 700 /home/${DEPLOY_USER}/.ssh
chmod 600 /home/${DEPLOY_USER}/.ssh/authorized_keys 2>/dev/null || true
chown -R ${DEPLOY_USER}:${DEPLOY_USER} /home/${DEPLOY_USER}/.ssh

echo ">> Instalando Docker + compose plugin..."
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi
usermod -aG docker "${DEPLOY_USER}"
systemctl enable --now docker

echo ">> Firewall (ufw)..."
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo ">> fail2ban..."
systemctl enable --now fail2ban

echo ">> Patches de segurança automáticos..."
dpkg-reconfigure -f noninteractive unattended-upgrades || true

echo ">> Endurecendo o SSH (só chave, sem root)..."
SSHD=/etc/ssh/sshd_config.d/99-hardening.conf
cat > "$SSHD" <<'EOF'
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
EOF
systemctl restart ssh || systemctl restart sshd || true

echo ""
echo "==================================================================="
echo " BOOTSTRAP CONCLUÍDO."
echo " AGORA, em OUTRO terminal, teste:  ssh ${DEPLOY_USER}@SEU_IP"
echo " Só feche esta sessão root depois de confirmar que o login funciona."
echo "==================================================================="
