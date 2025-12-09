#!/usr/bin/env python3
"""
R7 Trading Bot API - Deploy Automatico para Windows
Cria o arquivo tar.gz pronto para upload a AWS
"""

import subprocess
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
import tarfile

class DeployWindows:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.archive_name = f"r7-trading-bot-{self.timestamp}.tar.gz"
        
    def log(self, message, status="INFO"):
        """Log mensagens com timestamp"""
        prefix = f"[{status}]" if status else ""
        print(f"{prefix} {message}")
    
    def clean_cache(self):
        """Limpar cache Python"""
        self.log("Limpando cache Python...", "INFO")
        
        # Remover __pycache__
        for root, dirs, files in os.walk(self.project_root):
            if '__pycache__' in dirs:
                pycache = os.path.join(root, '__pycache__')
                shutil.rmtree(pycache)
                self.log(f"Removido: {pycache}", "OK")
        
        # Remover .pyc
        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                if file.endswith('.pyc'):
                    filepath = os.path.join(root, file)
                    os.remove(filepath)
                    self.log(f"Removido: {filepath}", "OK")
    
    def create_archive(self):
        """Criar arquivo tar.gz usando Python puro"""
        self.log("", "")
        self.log("=" * 60, "")
        self.log("CRIANDO ARQUIVO COMPACTADO", "INFO")
        self.log("=" * 60, "")
        
        # Limpar primeiro
        self.clean_cache()
        
        archive_path = self.project_root / self.archive_name
        
        self.log(f"Criando: {self.archive_name}", "INFO")
        
        # Exclusoes
        exclusions = {
            'venv_new', '__pycache__', '.git', '.env', 
            'temp_arquivos_antigos_excluir_10dez2025',
            'logs', 'deploy_', '.pytest_cache'
        }
        
        def filter_function(tarinfo):
            """Filtro para exclusoes"""
            path_parts = tarinfo.name.split('/')
            
            # Pular venv_new, __pycache__, etc
            for part in path_parts:
                if part in exclusions or part.endswith('.pyc'):
                    return None
            
            # Pular arquivos de log de deploy
            if 'deploy_' in tarinfo.name and tarinfo.name.endswith('.log'):
                return None
            
            return tarinfo
        
        try:
            with tarfile.open(str(archive_path), "w:gz") as tar:
                # Adicionar diretorio raiz
                tar.add(str(self.project_root), arcname="r7_v1", filter=filter_function)
            
            size_mb = archive_path.stat().st_size / (1024 * 1024)
            self.log(f"OK - {self.archive_name} ({size_mb:.2f} MB)", "SUCCESS")
            self.log(f"Caminho: {archive_path}", "INFO")
            return str(archive_path)
            
        except Exception as e:
            self.log(f"ERRO ao criar arquivo: {str(e)}", "ERROR")
            return None
    
    def show_next_steps(self):
        """Mostrar proximos passos"""
        self.log("", "")
        self.log("=" * 60, "")
        self.log("PROXIMOS PASSOS", "INFO")
        self.log("=" * 60, "")
        
        steps = """
1. REVOGAR CREDENCIAIS ANTIGAS (Binance):
   - URL: https://www.binance.com/en/account/api-management
   - Deletar as chaves antigas expostas
   - Confirmar revogacao

2. CRIAR NOVAS CREDENCIAIS (Binance):
   - Criar nova API Key
   - Copiar: API Key e Secret Key
   - Salvar em seguranca

3. CRIAR EC2 INSTANCE (AWS):
   - Abrir: https://console.aws.amazon.com/ec2
   - Name: r7-trading-bot-prod
   - AMI: Ubuntu 22.04 LTS
   - Type: t3.micro (Free Tier)
   - Security Group: Permitir portas 22, 8080, 8501
   - Download arquivo .pem (ex: r7-trading-bot-prod.pem)

4. UPLOAD E DEPLOY:
   - Abrir powershell
   - Executar comando abaixo com IP da EC2:
   
   scp -i "caminho_do_arquivo.pem" "{archive_path}" ubuntu@IP_EC2:~/r7-trading-bot.tar.gz
   
   ssh -i "caminho_do_arquivo.pem" ubuntu@IP_EC2
   
   # Na instancia:
   tar -xzf r7-trading-bot.tar.gz
   cd r7_v1
   bash setup_quick.sh
   
5. VERIFICAR:
   - curl http://IP_EC2:8080/api/health
   - Acessar dashboard: http://IP_EC2:8501

DOCUMENTACAO:
   - DEPLOY_QUICK.md (guia rapido)
   - AWS_DEPLOY_CHECKLIST.md (checklist completo)
   - REMEDIATION_SECURITY.md (seguranca)
"""
        print(steps)
    
    def run(self):
        """Executar deploy"""
        print("\n" + "=" * 60)
        print("R7 TRADING BOT API - DEPLOY AUTOMATICO")
        print("=" * 60 + "\n")
        
        archive_path = self.create_archive()
        
        if archive_path:
            self.log("ARQUIVO CRIADO COM SUCESSO", "SUCCESS")
            self.show_next_steps()
        else:
            self.log("FALHA NA CRIACAO DO ARQUIVO", "ERROR")
            sys.exit(1)

if __name__ == "__main__":
    deployer = DeployWindows()
    deployer.run()
