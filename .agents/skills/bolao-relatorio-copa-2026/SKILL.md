---
name: bolao-relatorio-copa-2026
description: >-
  Gera o relatório qualitativo estruturado dos jogos da Copa do Mundo de 2026, com os top 3 palpites matemáticos e estatísticas de acurácia.
---

# Relatório Qualitativo da Copa do Mundo 2026

## Overview
Esta skill local gera e exibe o relatório qualitativo estruturado dos jogos da Copa do Mundo de 2026. Ela roda o script de previsão tática e mostra os palpites matemáticos otimizados (top 3 placares por jogo), as análises táticas detalhadas e as métricas acumuladas de acurácia do modelo (conforme os resultados reais são inseridos).

## Dependencies
Esta skill requer que o ambiente virtual do Python esteja configurado no repositório.
- **Python 3**
- Script local [world_cup_manager.py](file:///home/rafa/Projects/bolao/world_cup_manager.py)
- Banco de dados em CSV [world_cup_2026.csv](file:///home/rafa/Projects/bolao/world_cup_2026.csv)

## Quick Start
Para testar a geração do relatório diretamente no terminal:
```bash
.venv/bin/python world_cup_manager.py --report
```

## Workflow
Sempre que o usuário digitar `/relatorio-copa-2026` ou pedir o relatório de jogos no chat:
1. Navegue até o diretório do projeto `/home/rafa/Projects/bolao/`.
2. Verifique se o ambiente virtual `.venv` está ativo ou use diretamente o executável `.venv/bin/python`.
3. Execute o comando para gerar o relatório qualitativo atualizado:
   ```bash
   .venv/bin/python world_cup_manager.py --report
   ```
4. Capture o output completo do comando.
5. Imprima o relatório qualitativo formatado em Markdown diretamente no chat para o usuário. Não resuma ou oculte informações; exiba o relatório completo incluindo o cabeçalho de métricas de desempenho.

## Common Mistakes
- **Não usar o executável do ambiente virtual**: Certifique-se de executar com `.venv/bin/python` para evitar falta de dependências importadas pelo script.
- **Esquecer de atualizar o CSV antes do relatório**: A execução de `--report` lê o estado atualizado do CSV, então as previsões exibidas serão baseadas nos últimos pesos calibrados em `settings.json`.
