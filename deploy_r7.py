#!/usr/bin/env python3
"""
🚀 R7 Trading Bot API - Deploy Automático
Executa todo o pipeline de deploy na AWS em um único script
"""

import subprocess
import os
import sys
import json
from datetime import datetime
from pathlib import Path

class DeployR7:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.archive_name = f"r7-trading-bot-{self.timestamp}.tar.gz"
        self.log_file = self.project_root / f"deploy_{self.timestamp}.log"
        
    def log(self, message, level="INFO"):
        """Log mensagens com timestamp"""
        log_msg = f"[{level}] {message}"
        print(log_msg)
        with open(self.log_file, 'a') as f:
            f.write(log_msg + "\n")
    
    def run_cmd(self, cmd, description=""):
        """Executar comando e retornar resultado"""
        try:
            self.log(f"Executando: {description or cmd}")
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                cwd=str(self.project_root)
            )
            if result.returncode != 0:
                self.log(f"ERRO ao executar: {description}", "ERROR")
                self.log(f"Stderr: {result.stderr}", "ERROR")
                return False
            self.log(f"✅ {description or cmd}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Exceção: {str(e)}", "ERROR")
            return False
    
    def step_1_create_archive(self):
        """PASSO 1: Criar arquivo compactado"""
        self.log("=" * 60)
        self.log("PASSO 1: Criando arquivo compactado", "INFO")
        self.log("=" * 60)
        
        # Limpar cache primeiro
        self.run_cmd(
            f'find "{self.project_root}" -type d -name __pycache__ -exec rm -rf {{}} +',
            "Limpando cache Python"
        )
        self.run_cmd(
            f'find "{self.project_root}" -name "*.pyc" -delete',
            "Removendo arquivos .pyc"
        )
        
        # Criar tar.gz
        tar_cmd = (
            f'tar --exclude="venv_new" '
            f'--exclude="__pycache__" '
            f'--exclude=".git" '
            f'--exclude="*.pyc" '
            f'--exclude=".env" '
            f'--exclude="data/audit/*" '
            f'--exclude="logs/*" '
            f'--exclude="temp_arquivos*" '
            f'-czf "{self.archive_name}" -C "{self.project_root.parent}" "{self.project_root.name}"'
        )
        
        if self.run_cmd(tar_cmd, "Compactando projeto"):
            archive_path = self.project_root / self.archive_name
            if archive_path.exists():
                size_mb = archive_path.stat().st_size / (1024 * 1024)
                self.log(f"✅ Arquivo criado: {self.archive_name} ({size_mb:.2f} MB)", "SUCCESS")
                return str(archive_path)
        
        self.log("❌ Falha ao criar arquivo", "ERROR")
        return None
    
    def step_2_show_deploy_info(self):
        """PASSO 2: Mostrar informações de deploy necessárias"""
        self.log("=" * 60)
        self.log("PASSO 2: Informações Necessárias para Deploy", "INFO")
        self.log("=" * 60)
        
        info = """
📋 PRÓXIMOS PASSOS - VOCÊ PRECISA FAZER NA AWS:

1️⃣  CRIAR EC2 INSTANCE:
   - AWS Console → EC2 → Launch Instance
   - Name: r7-trading-bot-prod
   - AMI: Ubuntu 22.04 LTS (Free Tier)
   - Instance type: t3.micro (FREE)
   - Key pair: r7-trading-bot-prod.pem (salvar em C:\\Users\\gabri\\.ssh\\)
   - Security Group: 
     * SSH (22): Seu IP
     * TCP (8080): 0.0.0.0/0
     * TCP (3000): 0.0.0.0/0
   - Storage: 20GB gp3
   - Launch

2️⃣  APÓS CRIAR EC2:
   - Copiar Public IPv4 (ex: 52.1.2.3)
   - Executar: python deploy_r7.py --deploy --ip <IP> --pem C:\\Users\\gabri\\.ssh\\r7-trading-bot-prod.pem

3️⃣  CRIAR S3 BUCKET (para backups):
   - AWS Console → S3 → Create bucket
   - Name: r7-trading-bot-backups-123456
   - Region: us-east-1

4️⃣  ARQUIVO PRONTO PARA UPLOAD:
   - {self.archive_name}
   - Tamanho: Verificar com: ls -lh {self.archive_name}

📧 DOCUMENTAÇÃO:
   - Deploy details: {self.log_file}
   - Checklist: AWS_DEPLOY_CHECKLIST.md
   - README: deploy/aws/README_AWS.md
"""
        self.log(info)
        print(info)
    
    def step_3_upload_and_deploy(self, ec2_ip, pem_path):
        """PASSO 3: Upload e deploy automático no servidor"""
        self.log("=" * 60)
        self.log("PASSO 3: Upload e Deploy Automático", "INFO")
        self.log("=" * 60)
        
        archive_path = self.project_root / self.archive_name
        
        if not archive_path.exists():
            self.log(f"❌ Arquivo não encontrado: {archive_path}", "ERROR")
            return False
        
        if not os.path.exists(pem_path):
            self.log(f"❌ Arquivo PEM não encontrado: {pem_path}", "ERROR")
            return False
        
        # 1. SSH Test
        self.log("Testando conexão SSH...", "INFO")
        ssh_test = f'ssh -i "{pem_path}" -o StrictHostKeyChecking=no ubuntu@{ec2_ip} "echo OK"'
        if not self.run_cmd(ssh_test, "Teste de conexão SSH"):
            return False
        
        # 2. Upload arquivo
        self.log("Iniciando upload do arquivo...", "INFO")
        scp_cmd = f'scp -i "{pem_path}" -o StrictHostKeyChecking=no "{archive_path}" ubuntu@{ec2_ip}:~/r7-trading-bot.tar.gz'
        if not self.run_cmd(scp_cmd, "Upload do arquivo"):
            return False
        
        # 3. Executar setup no servidor
        setup_script = """
set -e
echo "🚀 Iniciando setup do R7 Trading Bot API..."

# Atualizar sistema
echo "📦 Atualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar dependências
echo "🐍 Instalando Python e dependências..."
sudo apt install -y python3.11 python3.11-venv python3-pip git curl

# Criar diretório
echo "📁 Criando estrutura..."
mkdir -p ~/r7-trading-bot
cd ~/r7-trading-bot

# Extrair código
echo "📂 Extraindo código..."
tar -xzf ~/r7-trading-bot.tar.gz
rm ~/r7-trading-bot.tar.gz

# Criar ambiente virtual
echo "🔧 Criando venv..."
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências Python
echo "📚 Instalando requirements..."
pip install --upgrade pip
pip install -r requirements_new.txt 2>/dev/null || echo "⚠️ Alguns pacotes não encontrados"

# Criar arquivo .env
echo "⚙️  Criando .env..."
cat > .env << 'ENVEOF'
BINANCE_API_KEY=sua_api_key_aqui
BINANCE_API_SECRET=seu_secret_aqui
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
DEBUG=False
HOST=0.0.0.0
PORT=8080
DATABASE_PATH=data/app_leonardo.db
AWS_REGION=us-east-1
ENVEOF

# Criar diretórios de dados
mkdir -p data/{audit,metrics,backups,ai,cache,history}
mkdir -p logs
chmod 777 data logs

# Copiar serviços systemd
sudo cp deploy/aws/r7-trading-bot.service /etc/systemd/system/
sudo cp deploy/aws/r7-trading-dashboard.service /etc/systemd/system/

# Recarregar systemd
sudo systemctl daemon-reload
sudo systemctl enable r7-trading-bot.service
sudo systemctl enable r7-trading-dashboard.service

echo "✅ Setup concluído!"
echo "📋 Para iniciar os serviços, execute:"
echo "   sudo systemctl start r7-trading-bot.service"
echo "   sudo systemctl start r7-trading-dashboard.service"
echo "   sudo systemctl status r7-trading-bot.service"
"""
        
        self.log("Executando setup no servidor...", "INFO")
        setup_path = "/tmp/setup_r7.sh"
        
        # Salvar script localmente
        with open(setup_path, 'w') as f:
            f.write(setup_script)
        
        # Copiar script para servidor
        scp_setup = f'scp -i "{pem_path}" -o StrictHostKeyChecking=no "{setup_path}" ubuntu@{ec2_ip}:~/setup.sh'
        if not self.run_cmd(scp_setup, "Upload do script setup"):
            return False
        
        # Executar script
        ssh_setup = f'ssh -i "{pem_path}" -o StrictHostKeyChecking=no ubuntu@{ec2_ip} "bash ~/setup.sh"'
        if not self.run_cmd(ssh_setup, "Executando setup no servidor"):
            return False
        
        self.log("✅ Deploy concluído com sucesso!", "SUCCESS")
        return True
    
    def run(self, args):
        """Executar deploy"""
        print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║  🚀 R7 Trading Bot API - Deploy Automático na AWS             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
        """)
        
        # Passo 1: Criar arquivo
        archive = self.step_1_create_archive()
        if not archive:
            sys.exit(1)
        
        # Passo 2: Mostrar informações
        self.step_2_show_deploy_info()
        
        # Passo 3: Se passar --deploy
        if "--deploy" in args:
            try:
                ip_idx = args.index("--ip")
                pem_idx = args.index("--pem")
                ec2_ip = args[ip_idx + 1]
                pem_path = args[pem_idx + 1]
                
                if self.step_3_upload_and_deploy(ec2_ip, pem_path):
                    print("\n✅ DEPLOY SUCESSO! Acesse: http://" + ec2_ip + ":8080")
                else:
                    print("\n❌ Deploy falhou. Veja o log para detalhes.")
                    sys.exit(1)
            except (ValueError, IndexError):
                print("❌ Uso: python deploy_r7.py --deploy --ip <IP> --pem <CAMINHO_PEM>")
                sys.exit(1)
        
        print(f"\n📝 Log completo em: {self.log_file}")

if __name__ == "__main__":
    deployer = DeployR7()
    deployer.run(sys.argv)
