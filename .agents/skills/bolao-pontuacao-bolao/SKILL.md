---
name: bolao-pontuacao-bolao
description: >-
  Calcula quantos pontos o modelo de consenso obteve no bolão aplicando as regras oficiais de pontuação (resultado, placar exato, bônus de gols de um time, campeão e artilheiro).
---

# Pontuação do Modelo no Bolão

## Overview
Esta skill local calcula e exibe a pontuação total acumulada pelo modelo preditivo no bolão de acordo com as regras de pontuação definidas.

## Dependencies
Esta skill requer que o ambiente virtual do Python esteja configurado no repositório.
- **Python 3**
- Script local [world_cup_manager.py](file:///home/rafa/Projects/bolao/world_cup_manager.py)
- Banco de dados em CSV [world_cup_2026.csv](file:///home/rafa/Projects/bolao/world_cup_2026.csv)

## Quick Start
Para testar a geração da pontuação diretamente no terminal:
```bash
PYTHONPATH=. .venv/bin/python world_cup_manager.py --bolao
```

## Workflow
Sempre que o usuário digitar `/pontuacao-bolao` ou pedir para calcular os pontos do modelo no bolão:
1. Navegue até o diretório do projeto `/home/rafa/Projects/bolao/`.
2. Execute o comando para calcular a pontuação atualizada:
   ```bash
   PYTHONPATH=. .venv/bin/python world_cup_manager.py --bolao
   ```
3. Capture o output completo do comando.
4. Imprima o relatório de pontuação formatado em Markdown diretamente no chat para o usuário.

## Rules Applied
- **Resultado Correto (Vitória ou Empate)**: +2 pontos (se não acertar o placar exato).
- **Placar Exato**: +5 pontos (não soma com o bônus de resultado ou de gols).
- **Bônus de Gols de um Time**: +1 ponto (apenas se acertar o vencedor e cravar os gols de uma das equipes; placar exato não soma o bônus).
- **Campeão Indicado**: +10 pontos (quando finalizado).
- **Artilheiro Indicado**: +8 pontos (quando finalizado).
