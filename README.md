# Análise Empírica de Algoritmos de Ordenação

Trabalho 1 — Análise de Algoritmos — IGCE/UNESP
Prof. Daniel Pedronette

**Grupo:**
- Fábio Almeida de Siqueira
- Jorge Fernando Ferreira da Silva
- Miguel Ribeiro Dantas de Alencar Fugita

## Algoritmos

| Algoritmo | Melhor caso | Caso médio | Pior caso | Observação |
|---|---|---|---|---|
| Insertion Sort | O(n) | O(n²) | O(n²) | melhor caso: vetor ordenado |
| Selection Sort | O(n²) | O(n²) | O(n²) | sempre n(n−1)/2 comparações |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | memória auxiliar O(n) |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | in-place |
| Quick Sort | O(n log n) | O(n log n) | O(n²) | Lomuto, pivô = último elemento |
| Quick Sort MM | O(n log n) | O(n log n) | O(n log n) | pivô = mediana das medianas (BFPRT) |

## Estrutura

```
src/sort.c           implementação dos algoritmos e do experimento
analise/analise.py   estatísticas (pandas) e gráficos (matplotlib)
dados/               CSVs brutos gerados pelo experimento
resultados/          tabelas resumo (média, desvio padrão, IC95, expoentes)
graficos/            figuras usadas no relatório e nos slides
relatorio/  slides/  material de entrega
```

## Como reproduzir

Requisitos: gcc (Linux ou WSL), Python 3 com pandas, numpy e matplotlib.

```bash
make            # compila ./tempo e ./ops
make dados      # executa o experimento (alguns minutos)
make analise    # gera resultados/ e graficos/
```

Sem `make`:

```bash
gcc -O2 -Wall -o tempo src/sort.c
gcc -O2 -Wall -DCONTAR -o ops src/sort.c
./tempo > dados/tempos.csv
./ops   > dados/operacoes.csv
python3 analise/analise.py
```

## Metodologia

- Todos os algoritmos em C, mesmo compilador e mesmas flags (`-O2`).
- Mesma entrada para todos: o vetor é gerado uma vez por repetição (gerador xorshift32 com semente fixa) e copiado para cada algoritmo.
- Tempo medido com `clock_gettime(CLOCK_MONOTONIC)`; contagem de comparações e movimentos em compilação separada (`-DCONTAR`) para não interferir no tempo.
- Tamanhos: 1.000 a 1.000.000 (progressão geométrica); casos O(n²) limitados a n = 50.000.
- Entradas: aleatória, ordenada, inversa e quase ordenada (5% de trocas aleatórias).
- 10 repetições por configuração; média, desvio padrão, coeficiente de variação e IC 95%.
- Toda execução verifica se o vetor resultante está ordenado.
- A contagem de operações é determinística e independente da máquina; o tempo foi medido em uma única máquina (abaixo).

## Ambiente de execução (preencher)

| Item | Valor |
|---|---|
| CPU | |
| RAM | |
| Sistema operacional | |
| Compilador | gcc x.y |
| Flags | -O2 -Wall |
| Data da coleta | |

## Observação sobre o Quick Sort MM

A mediana das medianas garante que o pivô separa pelo menos ~30% dos elementos de cada lado,
eliminando o pior caso O(n²). Em contrapartida, a seleção do pivô tem custo linear com constante
alta, então em entradas aleatórias ele tende a ser mais lento que o Quick Sort clássico.
Os dados foram gerados com poucos elementos repetidos; com muitos valores iguais, a partição
de Lomuto desbalanceia independentemente do pivô.
