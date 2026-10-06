#!/usr/bin/env bash
# rodar_noite.sh - Coleta longa (para deixar rodando durante a noite)
#
#   tempo:     20 repeticoes
#   operacoes:  5 repeticoes (as contagens quase nao variam)
#   n ate 10.000.000; casos O(n^2) ate 500.000 (estimativa: ~9 h)
#
# Uso (na raiz do repositorio, pelo Git Bash ou Linux):  bash rodar_noite.sh
# Progresso em dados/coleta.log. Cada linha dos CSVs e gravada na hora,
# entao uma interrupcao nao perde o que ja foi medido.

set -u
cd "$(dirname "$0")"

command -v gcc > /dev/null || export PATH="/c/MinGW/bin:$PATH"

PARAMS="-DN_MAX=10000000 -DN_MAX_QUAD=500000"
gcc -O2 -Wall $PARAMS -DREPETICOES=20 -o tempo src/sort.c || exit 1
gcc -O2 -Wall $PARAMS -DREPETICOES=5 -DCONTAR -o ops src/sort.c || exit 1

mkdir -p dados
LOG=dados/coleta.log
echo "== coleta iniciada em $(date '+%d/%m/%Y %H:%M:%S')" | tee "$LOG"

echo "== tempo (20 repeticoes)" | tee -a "$LOG"
./tempo > dados/tempos.csv 2> >(tee -a "$LOG" >&2)
rc=$?
echo "== tempo terminado em $(date '+%H:%M:%S') (codigo $rc)" | tee -a "$LOG"

echo "== operacoes (5 repeticoes)" | tee -a "$LOG"
./ops > dados/operacoes.csv 2> >(tee -a "$LOG" >&2)
rc=$?
echo "== operacoes terminado em $(date '+%H:%M:%S') (codigo $rc)" | tee -a "$LOG"

echo "== coleta concluida em $(date '+%d/%m/%Y %H:%M:%S')" | tee -a "$LOG"
read -r -p "Pode fechar esta janela (Enter)."
