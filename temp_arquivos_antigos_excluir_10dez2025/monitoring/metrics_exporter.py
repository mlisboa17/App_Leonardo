"""
📊 Metrics Exporter - App Leonardo
Envia métricas do bot para o InfluxDB/Grafana
"""

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
import os
import json
import time
import threading

class MetricsExporter:
    """Exporta métricas do trading bot para InfluxDB"""
    
    def __init__(self, url="http://localhost:8086", token="leonardo-trading-token-2024", 
                 org="leonardo", bucket="trading"):
        """
        Inicializa o exportador de métricas
        
        Args:
            url: URL do InfluxDB
            token: Token de autenticação
            org: Organização no InfluxDB
            bucket: Bucket para armazenar dados
        """
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client = None
        self.write_api = None
        self._connected = False
        self._export_interval = 10  # segundos
        self._running = False
        
    def connect(self):
        """Conecta ao InfluxDB"""
        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            
            # Testa conexão
            health = self.client.health()
            if health.status == "pass":
                self._connected = True
                print(f"✅ Conectado ao InfluxDB: {self.url}")
                return True
            else:
                print(f"⚠️ InfluxDB status: {health.status}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao conectar ao InfluxDB: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Desconecta do InfluxDB"""
        if self.client:
            self.client.close()
            self._connected = False
            print("🔌 Desconectado do InfluxDB")
    
    def export_balance(self, usdt_balance: float, total_crypto_value: float, total_value: float):
        """
        Exporta dados de saldo
        
        Args:
            usdt_balance: Saldo em USDT
            total_crypto_value: Valor total em crypto (USD)
            total_value: Patrimônio total
        """
        if not self._connected:
            return False
            
        try:
            point = Point("balance") \
                .tag("bot", "leonardo") \
                .field("usdt", float(usdt_balance)) \
                .field("crypto_value", float(total_crypto_value)) \
                .field("total", float(total_value)) \
                .time(datetime.utcnow(), WritePrecision.NS)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
            
        except Exception as e:
            print(f"❌ Erro ao exportar saldo: {e}")
            return False
    
    def export_trade(self, symbol: str, side: str, amount: float, price: float, 
                     pnl: float = 0, profit_pct: float = 0):
        """
        Exporta dados de um trade
        
        Args:
            symbol: Par de trading (ex: BTC/USDT)
            side: buy ou sell
            amount: Quantidade
            price: Preço
            pnl: Lucro/Prejuízo em USD
            profit_pct: Lucro/Prejuízo em percentual
        """
        if not self._connected:
            return False
            
        try:
            point = Point("trades") \
                .tag("bot", "leonardo") \
                .tag("symbol", symbol) \
                .tag("side", side) \
                .field("amount", float(amount)) \
                .field("price", float(price)) \
                .field("pnl", float(pnl)) \
                .field("profit_pct", float(profit_pct)) \
                .time(datetime.utcnow(), WritePrecision.NS)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
            
        except Exception as e:
            print(f"❌ Erro ao exportar trade: {e}")
            return False
    
    def export_stats(self, daily_pnl: float, total_trades: int, wins: int, 
                     losses: int, win_rate: float):
        """
        Exporta estatísticas do bot
        
        Args:
            daily_pnl: Lucro/Prejuízo do dia
            total_trades: Total de trades
            wins: Trades vencedores
            losses: Trades perdedores
            win_rate: Taxa de acerto (%)
        """
        if not self._connected:
            return False
            
        try:
            point = Point("stats") \
                .tag("bot", "leonardo") \
                .field("daily_pnl", float(daily_pnl)) \
                .field("total_trades", int(total_trades)) \
                .field("wins", int(wins)) \
                .field("losses", int(losses)) \
                .field("win_rate", float(win_rate)) \
                .time(datetime.utcnow(), WritePrecision.NS)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
            
        except Exception as e:
            print(f"❌ Erro ao exportar stats: {e}")
            return False
    
    def export_crypto_price(self, symbol: str, price: float, change_24h: float = 0):
        """
        Exporta preço de uma criptomoeda
        
        Args:
            symbol: Símbolo (ex: BTC)
            price: Preço atual em USD
            change_24h: Variação 24h em %
        """
        if not self._connected:
            return False
            
        try:
            point = Point("prices") \
                .tag("symbol", symbol) \
                .field("price", float(price)) \
                .field("change_24h", float(change_24h)) \
                .time(datetime.utcnow(), WritePrecision.NS)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
            
        except Exception as e:
            print(f"❌ Erro ao exportar preço: {e}")
            return False
    
    def export_portfolio(self, holdings: dict):
        """
        Exporta composição do portfólio
        
        Args:
            holdings: Dict com {symbol: value_usd}
        """
        if not self._connected:
            return False
            
        try:
            for symbol, value in holdings.items():
                point = Point("portfolio") \
                    .tag("bot", "leonardo") \
                    .tag("symbol", symbol) \
                    .field("value_usd", float(value)) \
                    .time(datetime.utcnow(), WritePrecision.NS)
                
                self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao exportar portfólio: {e}")
            return False


# Instância global
_metrics_exporter = None

def get_metrics_exporter() -> MetricsExporter:
    """Retorna instância singleton do MetricsExporter"""
    global _metrics_exporter
    
    if _metrics_exporter is None:
        _metrics_exporter = MetricsExporter()
        _metrics_exporter.connect()
    
    return _metrics_exporter


def export_all_metrics(balance_data: dict, stats_data: dict, prices_data: dict):
    """
    Função helper para exportar todas as métricas de uma vez
    
    Args:
        balance_data: {'usdt': float, 'crypto_value': float, 'total': float}
        stats_data: {'daily_pnl': float, 'trades': int, 'wins': int, 'losses': int, 'win_rate': float}
        prices_data: {'BTC': {'price': float, 'change_24h': float}, ...}
    """
    exporter = get_metrics_exporter()
    
    if not exporter._connected:
        return
    
    # Exporta saldo
    if balance_data:
        exporter.export_balance(
            balance_data.get('usdt', 0),
            balance_data.get('crypto_value', 0),
            balance_data.get('total', 0)
        )
    
    # Exporta stats
    if stats_data:
        exporter.export_stats(
            stats_data.get('daily_pnl', 0),
            stats_data.get('trades', 0),
            stats_data.get('wins', 0),
            stats_data.get('losses', 0),
            stats_data.get('win_rate', 0)
        )
    
    # Exporta preços
    if prices_data:
        for symbol, data in prices_data.items():
            if isinstance(data, dict):
                exporter.export_crypto_price(
                    symbol,
                    data.get('price', 0),
                    data.get('change_24h', 0)
                )
            else:
                exporter.export_crypto_price(symbol, data, 0)


if __name__ == "__main__":
    # Teste
    print("🧪 Testando conexão com InfluxDB...")
    
    exporter = MetricsExporter()
    if exporter.connect():
        print("✅ Conexão OK!")
        
        # Exporta dados de teste
        exporter.export_balance(10000, 5000, 15000)
        exporter.export_stats(50, 10, 7, 3, 70.0)
        exporter.export_crypto_price("BTC", 95000, 2.5)
        exporter.export_crypto_price("ETH", 3500, -1.2)
        
        print("✅ Dados de teste exportados!")
        
        exporter.disconnect()
    else:
        print("❌ Falha na conexão. Certifique-se que o InfluxDB está rodando.")
        print("   Execute: docker-compose up -d")
