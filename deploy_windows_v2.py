#!/usr/bin/env python3
"""
🚀 R7 Trading Bot - Deploy para AWS (Versão Windows)
Deploy automático do projeto para EC2 na AWS
"""

import subprocess
import os
import sys
import json
from datetime import datetime
from pathlib import Path
import shutil

class DeployR7Windows:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.archive_name = f"r7-trading-bot-{self.timestamp}.zip"
        self.log_file = self.project_root / f"deploy_{self.timestamp}.log"
        self.aws_region = "us-east-1"
        self.ec2_instance_ip = "18.230.59.118"  # IP do seu EC2
        
    def log(self, message, level="INFO"):
        """Log mensagens com timestamp"""
        log_msg = f"[{level}] {message}"
        print(log_msg)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_msg + "\n")
    
    def step_1_prepare_files(self):
        """PASSO 1: Preparar arquivos para deploy"""
        self.log("=" * 70)
        self.log("PASSO 1: Preparando arquivos para deploy", "INFO")
        self.log("=" * 70)
        
        # Criar pasta temporária
        deploy_folder = self.project_root / "deploy_temp"
        if deploy_folder.exists():
            shutil.rmtree(deploy_folder)
        deploy_folder.mkdir()
        
        self.log(f"📁 Pasta de deploy criada: {deploy_folder}", "SUCCESS")
        
        # Copiar arquivos principais
        files_to_copy = [
            "config/",
            "data/",
            "frontend/",
            "requirements.txt",
            "main_multibot.py",
            "adaptive_bot_system.py",
            "ai_orchestrator.py",
            "capital_manager.py",
            "market_monitor.py",
            ".env"
        ]
        
        for file_pattern in files_to_copy:
            source = self.project_root / file_pattern
            if source.exists():
                if source.is_dir():
                    dest = deploy_folder / file_pattern
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(source, dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
                    self.log(f"✅ Copiada pasta: {file_pattern}", "SUCCESS")
                else:
                    dest = deploy_folder / file_pattern
                    shutil.copy2(source, dest)
                    self.log(f"✅ Copiado arquivo: {file_pattern}", "SUCCESS")
            else:
                self.log(f"⚠️ Arquivo não encontrado: {file_pattern}", "WARNING")
        
        return deploy_folder
    
    def step_2_create_archive(self, deploy_folder):
        """PASSO 2: Criar arquivo ZIP"""
        self.log("=" * 70)
        self.log("PASSO 2: Criando arquivo ZIP", "INFO")
        self.log("=" * 70)
        
        try:
            archive_path = self.project_root / self.archive_name
            if archive_path.exists():
                archive_path.unlink()
            
            # Usar shutil para criar ZIP
            shutil.make_archive(
                str(self.project_root / self.archive_name[:-4]),  # Remove .zip
                'zip',
                str(deploy_folder)
            )
            
            if archive_path.exists():
                size_mb = archive_path.stat().st_size / (1024 * 1024)
                self.log(f"✅ Arquivo criado: {self.archive_name} ({size_mb:.2f} MB)", "SUCCESS")
                return str(archive_path)
            else:
                self.log("❌ Falha ao criar arquivo ZIP", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Erro ao criar ZIP: {str(e)}", "ERROR")
            return None
    
    def step_3_show_deployment_info(self):
        """PASSO 3: Mostrar informações de deploy"""
        self.log("=" * 70)
        self.log("PASSO 3: Instruções de Deploy", "INFO")
        self.log("=" * 70)
        
        info = f"""
╔════════════════════════════════════════════════════════════════════╗
║           🚀 DEPLOYMENT DO R7 TRADING BOT - RESUMO                 ║
╚════════════════════════════════════════════════════════════════════╝

📦 ARQUIVO DE DEPLOY:
   Caminho: {self.project_root / self.archive_name}
   Tamanho: Verifique o tamanho do arquivo

🌐 INFORMAÇÕES AWS:
   Region: {self.aws_region}
   EC2 Instance: {self.ec2_instance_ip}
   
📋 PRÓXIMOS PASSOS:

1️⃣  FAZER UPLOAD DO ARQUIVO PARA EC2:
   
   Usando SCP (Linux/Mac):
   scp -i "seu-pem-key.pem" \\
       "{self.project_root / self.archive_name}" \\
       ubuntu@{self.ec2_instance_ip}:/tmp/
   
   Usando WinSCP (Windows GUI):
   - Abra WinSCP
   - New Site
   - Host: {self.ec2_instance_ip}
   - User: ubuntu
   - Private Key: seu-pem-key.pem
   - Upload o arquivo para /tmp/

2️⃣  CONECTAR NO EC2 VIA SSH:
   
   ssh -i "seu-pem-key.pem" ubuntu@{self.ec2_instance_ip}

3️⃣  DESCOMPACTAR E INSTALAR NO EC2:
   
   cd /tmp
   unzip -q {self.archive_name}
   cd r7-trading-bot-{self.timestamp}
   
4️⃣  CRIAR AMBIENTE VIRTUAL:
   
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt

5️⃣  CONFIGURAR ARQUIVO .env:
   
   nano .env
   # Adicione suas credenciais e configurações

6️⃣  INICIAR O BOT:
   
   # Terminal 1 - Dashboard Streamlit:
   streamlit run frontend/dashboard_multibot.py --server.port 8501
   
   # Terminal 2 - AI Orchestrator:
   python ai_orchestrator.py
   
   # Terminal 3 - Main Bot:
   python main_multibot.py

7️⃣  ACESSAR NO NAVEGADOR:
   
   Dashboard: http://{self.ec2_instance_ip}:8501
   API: http://{self.ec2_instance_ip}:8000

✅ VERIFICAR LOGS:
   tail -f logs/coordinator.log
   tail -f logs/dashboard.log

📊 DADOS IMPORTANTES:
   - Config: /r7-trading-bot/config/bots_config.yaml
   - Dados: /r7-trading-bot/data/
   - Logs: /r7-trading-bot/logs/

⚠️  REMINDERS:
   - Atualizar credenciais no .env
   - Configurar firewall para port 8501 e 8000
   - Backup dos dados antes de cada deploy
   - Monitorar logs constantemente

════════════════════════════════════════════════════════════════════
"""
        print(info)
        self.log(info, "INFO")
    
    def step_4_create_deployment_guide(self):
        """PASSO 4: Criar guia de deployment"""
        self.log("=" * 70)
        self.log("PASSO 4: Criando guia de deployment", "INFO")
        self.log("=" * 70)
        
        guide = f"""# 🚀 Guia de Deployment R7 Trading Bot

## 📋 Informações do Deploy

- **Data**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Arquivo**: {self.archive_name}
- **Região AWS**: {self.aws_region}
- **EC2 IP**: {self.ec2_instance_ip}

## 🔑 Pré-requisitos

1. **Chave PEM (.pem)**
   - Arquivo: seu-pem-key.pem
   - Permissões: chmod 400 seu-pem-key.pem

2. **Ferramentas**
   - SSH Client
   - SCP ou WinSCP
   - Terminal/PowerShell

## 📦 Conteúdo do Deploy

```
r7-trading-bot/
├── config/                  # Configurações dos bots
├── data/                    # Dados persistentes
├── frontend/               # Dashboard Streamlit
├── requirements.txt        # Dependências Python
├── main_multibot.py       # Bot principal
├── adaptive_bot_system.py # Sistema adaptativo
├── ai_orchestrator.py     # Orquestrador IA
└── .env                   # Variáveis de ambiente
```

## 🚀 Passo a Passo

### 1. Upload do Arquivo

**Via SCP (Recomendado):**
```bash
scp -i "seu-pem-key.pem" \\
    "{self.archive_name}" \\
    ubuntu@{self.ec2_instance_ip}:/tmp/
```

**Via WinSCP (GUI):**
- Abra WinSCP
- New Site → SFTP
- Host: {self.ec2_instance_ip}
- User: ubuntu
- Private Key: seu-pem-key.pem
- Drag & drop o arquivo

### 2. Conectar no EC2

```bash
ssh -i "seu-pem-key.pem" ubuntu@{self.ec2_instance_ip}
```

### 3. Descompactar

```bash
cd /tmp
unzip -q {self.archive_name}
cd r7-trading-bot
```

### 4. Criar Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

### 5. Configurar Credenciais

```bash
nano .env
```

Adicione:
```
BINANCE_API_KEY=seu_api_key
BINANCE_API_SECRET=seu_api_secret
TELEGRAM_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id
AWS_ACCESS_KEY_ID=seu_aws_key
AWS_SECRET_ACCESS_KEY=seu_aws_secret
```

### 6. Iniciar Serviços

**Em terminais separados:**

Terminal 1 - Dashboard:
```bash
source venv/bin/activate
streamlit run frontend/dashboard_multibot.py --server.port 8501 --server.address 0.0.0.0
```

Terminal 2 - AI Orchestrator:
```bash
source venv/bin/activate
python ai_orchestrator.py
```

Terminal 3 - Main Bot:
```bash
source venv/bin/activate
python main_multibot.py
```

### 7. Acessar

- Dashboard: http://{self.ec2_instance_ip}:8501
- API: http://{self.ec2_instance_ip}:8000

## 📊 Monitoramento

```bash
# Logs em tempo real
tail -f logs/coordinator.log

# Verificar espaço em disco
df -h

# Verificar uso de memória
free -h

# Processos do bot
ps aux | grep python
```

## 🔧 Troubleshooting

### Porta já em uso
```bash
lsof -i :8501
kill -9 <PID>
```

### Erro de dependências
```bash
pip install --upgrade -r requirements.txt
```

### Problema com permissões
```bash
chmod +x *.py
```

## 🔐 Segurança

1. ✅ Mude a senha padrão do ubuntu
2. ✅ Configure firewall (allow only necessary ports)
3. ✅ Use PM2 ou Supervisor para gerenciar processos
4. ✅ Backups diários de data/
5. ✅ Monitore logs constantemente

## 📞 Suporte

- Verifique logs em `/logs/`
- Consulte `config/bots_config.yaml`
- Teste conexão com Binance antes de operar

"""
        
        guide_path = self.project_root / f"DEPLOYMENT_GUIDE_{self.timestamp}.md"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide)
        
        self.log(f"✅ Guia de deployment criado: {guide_path}", "SUCCESS")
        return guide_path
    
    def cleanup(self, deploy_folder):
        """Limpar pasta temporária"""
        try:
            if deploy_folder.exists():
                shutil.rmtree(deploy_folder)
                self.log("✅ Pasta temporária removida", "SUCCESS")
        except Exception as e:
            self.log(f"⚠️ Erro ao limpar: {str(e)}", "WARNING")
    
    def run(self):
        """Executar deployment completo"""
        print("\n")
        print("╔" + "=" * 68 + "╗")
        print("║" + " " * 20 + "🚀 R7 TRADING BOT - DEPLOY AWS" + " " * 18 + "║")
        print("║" + " " * 15 + "Versão Windows com suporte a ZIP" + " " * 22 + "║")
        print("╚" + "=" * 68 + "╝")
        print()
        
        try:
            # Passo 1: Preparar arquivos
            deploy_folder = self.step_1_prepare_files()
            
            # Passo 2: Criar arquivo
            archive_path = self.step_2_create_archive(deploy_folder)
            
            if archive_path:
                # Passo 3: Informações de deployment
                self.step_3_show_deployment_info()
                
                # Passo 4: Criar guia
                guide_path = self.step_4_create_deployment_guide()
                
                self.log("=" * 70)
                self.log("✅ PRÉ-DEPLOYMENT CONCLUÍDO COM SUCESSO!", "SUCCESS")
                self.log("=" * 70)
                print(f"\n✅ Arquivo pronto para upload: {archive_path}\n")
                print(f"📄 Guia completo: {guide_path}\n")
                
            else:
                self.log("❌ Falha no pré-deployment", "ERROR")
                sys.exit(1)
                
        except Exception as e:
            self.log(f"❌ Erro geral: {str(e)}", "ERROR")
            sys.exit(1)
        finally:
            # Limpar
            if 'deploy_folder' in locals():
                self.cleanup(deploy_folder)


if __name__ == "__main__":
    deployer = DeployR7Windows()
    deployer.run()
