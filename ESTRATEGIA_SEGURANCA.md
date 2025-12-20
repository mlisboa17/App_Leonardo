# ESTRATEGIA_SEGURANCA

Este documento descreve as regras de segurança e mitigação de riscos operacionais do R7 Trading Bot.

## 1) Trava Estrita da SMA200 ✅
- Regra: **Não abrir novas posições de compra** para qualquer símbolo cujo preço esteja abaixo da SMA200. A política é global — sem exceções. 
- Quando a SMA200 bloquear uma operação, registra-se um evento de auditoria e incrementa-se o contador diário de bloqueios (SMA blocks).

## 2) Regra 50/50 (Lucro Semanal) ⚖️
- Objetivo: ao final de cada semana (domingo 23:59 BRT), o lucro apurado será dividido 50/50 entre stakeholders e reserva de capital (ou conforme política definida). 
- Implementação operacional: gerar relatório semanal e sinalizar contabilidade automaticamente para execução manual (por segurança).

## 3) Meta Diária — 1% | $20.00 🎯
- Base: **Capital Inicial = $2,000.00**
- Meta: **1% ao dia → $20.00/dia**
- Considerações: o sistema reporta progresso diário no dashboard; caso o dia esteja negativo a meta passa por política de recuperação automática (aumenta-se proporção em próximos dias até meta semanal).

## 4) Filtro de Volume — Priorizar Top20 da Binance 📈
- Para reduzir risco de alta volatilidade, o sistema **prioriza** ativos do Top 20 por volume na Binance. 
- O processo busca automaticamente os Top20 e atualiza a lista de símbolos do `config/config.yaml` (ferramenta: `tools/update_top20_symbols.py`).

## 5) Procedimentos de Crise (Ações rápidas) 🛠️
- Se *drawdown diário* ultrapassar configuração `safety.max_daily_loss` (p.ex. 1.5%), o sistema aciona a *trava total* e pausa aberturas de novas posições. 
- Em caso de *queda de saldo* superior a 2% em janela curta, o Balance Watcher envia alerta ao Telegram e o operador avalia intervenção manual.
- Há um processo de auditoria e export de logs para investigar ações que precederam a crise.

## 6) Logs & Auditoria 🧾
- Todos eventos de segurança (SMA blocks, overrides de capital, halts) devem ser registrados com timestamp e enviados ao Telegram em resumo diário.

> Nota: Este documento será armazenado em `ESTRATEGIA_SEGURANCA.md` no repositório raiz e referenciado no README do projeto.
