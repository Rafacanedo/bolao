---
name: bolao-relatorio-copa-2026
description: >-
  Gera o relatório qualitativo estruturado dos jogos da Copa do Mundo de 2026, com os top 3 palpites matemáticos, estatísticas de acurácia, e linhas de under/over 2.5 e ambos marcam.
---

# Relatório Qualitativo da Copa do Mundo 2026

## Overview
Esta skill local gera e exibe o relatório qualitativo estruturado dos jogos da Copa do Mundo de 2026. Ela roda o script de previsão tática e mostra os palpites matemáticos otimizados (top 3 placares por jogo), as linhas e odds de under/over 2.5 e ambos marcam (BTTS), as análises táticas detalhadas e as métricas acumuladas de acurácia do modelo (conforme os resultados reais são inseridos).

## Dependencies
Esta skill requer que o ambiente virtual do Python esteja configurado no repositório.
- **Python 3**
- Script local [world_cup_manager.py](file:///home/rafa/Projects/bolao/world_cup_manager.py)
- Banco de dados em CSV [world_cup_2026.csv](file:///home/rafa/Projects/bolao/world_cup_2026.csv)

## Quick Start
Para testar a geração do relatório diretamente no terminal:
```bash
# Relatório de hoje
.venv/bin/python world_cup_manager.py --report

# Relatório filtrado por seleção e status
.venv/bin/python world_cup_manager.py --report --team Espanha --status SCHEDULED

# Relatório de uma rodada inteira
.venv/bin/python world_cup_manager.py --report --stage "Round 2"
```

## Workflow
Sempre que o usuário digitar `/relatorio-copa-2026` ou pedir o relatório de jogos no chat:
1. Navegue até o diretório do projeto `/home/rafa/Projects/bolao/`.
2. Verifique se o ambiente virtual `.venv` está ativo ou use diretamente o executável `.venv/bin/python`.
3. Execute o comando para gerar o relatório qualitativo com os filtros especificados pelo usuário (caso aplique):
   ```bash
   .venv/bin/python world_cup_manager.py --report [filtros]
   ```
4. Capture o output completo do comando.
5. Imprima o relatório qualitativo formatado em Markdown diretamente no chat para o usuário. Não resuma ou oculte informações; exiba o relatório completo incluindo o cabeçalho de métricas de desempenho.

## Options & Filters
O script `--report` suporta as seguintes flags de filtragem:
- `--date YYYY-MM-DD`: Filtra os jogos por data específica (padrão é hoje se nenhuma outra flag de filtro for informada).
- `--team <nome>`: Filtra apenas os jogos da seleção informada (ex: `--team Uruguai`).
- `--stage <fase>`: Filtra jogos de uma fase ou rodada específica (ex: `--stage "Round 2"`).
- `--status <status>`: Filtra jogos pelo status (ex: `--status SCHEDULED` ou `--status FINISHED`).

## Features
- **Limpeza Visual**: Oculta seções de texto vazias (opiniões dos profissionais, resenha e clima) e odds secundárias de bookmakers que estejam zeradas/N/A.
- **Visualização Compacta**: Exibe partidas finalizadas (`FINISHED`) em uma única linha compacta de resumo.
- **Emojis Automáticos**: As bandeiras/emojis são puxados dinamicamente do banco de dados SQLite (`world_cup_teams`) caso estejam vazias no JSON.
- **Métricas de Confiança e Risco**: 
  - *Nível de Confiança*: Calculado a partir da probabilidade consensual do modelo para o resultado dominante.
  - *Fator de Risco*: Calculado com base no desvio padrão (divergência) de opiniões entre todas as fontes do ensemble do modelo.

## Common Mistakes
- **Não usar o executável do ambiente virtual**: Certifique-se de executar com `.venv/bin/python` para evitar falta de dependências importadas pelo script.
- **Esquecer de atualizar o CSV antes do relatório**: A execução de `--report` lê o estado atualizado do CSV, então as previsões exibidas serão baseadas nos últimos pesos calibrados em `settings.json`.
