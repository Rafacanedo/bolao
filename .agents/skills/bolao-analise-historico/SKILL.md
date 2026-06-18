---
name: bolao-analise-historico
description: >-
  Gera o relatório quantitativo de desempenho histórico do modelo, mostrando acertos de vencedor/empate (H/D/A) e placar exato para jogos finalizados da Copa de 2026.
---

# Relatório Histórico de Desempenho da Copa do Mundo 2026

## Overview
Esta skill local gera e exibe o relatório de desempenho histórico acumulado das previsões do modelo de consenso contra os resultados reais que já aconteceram no torneio.

## Dependencies
Esta skill requer que o ambiente virtual do Python esteja configurado no repositório.
- **Python 3**
- Script local [world_cup_manager.py](file:///home/rafa/Projects/bolao/world_cup_manager.py)
- Banco de dados em CSV [world_cup_2026.csv](file:///home/rafa/Projects/bolao/world_cup_2026.csv)

## Quick Start
Para testar a geração do relatório diretamente no terminal:
```bash
PYTHONPATH=. .venv/bin/python world_cup_manager.py --history
```

## Workflow
Sempre que o usuário digitar `/analise-historico` ou pedir o relatório histórico de previsões no chat:
1. Navegue até o diretório do projeto `/home/rafa/Projects/bolao/`.
2. Execute o comando para gerar o relatório quantitativo atualizado:
   ```bash
   PYTHONPATH=. .venv/bin/python world_cup_manager.py --history
   ```
3. Capture o output completo do comando.
4. Imprima o relatório histórico formatado em Markdown diretamente no chat para o usuário. Não oculte informações; exiba o relatório completo incluindo as métricas acumuladas de acurácia.

## Common Mistakes
- **Não definir PYTHONPATH**: O script `world_cup_manager.py` precisa importar módulos do diretório atual, então defina `PYTHONPATH=.` ou execute a partir da pasta raiz.
- **Não usar o executável do ambiente virtual**: Certifique-se de executar com `.venv/bin/python` para evitar falta de dependências.
