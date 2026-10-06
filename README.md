# Análise Empírica de Algoritmos de Ordenação

Trabalho 1 — Análise de Algoritmos — IGCE/UNESP<br>
Prof. Daniel Pedronette

**Grupo:**
- Fábio Almeida de Siqueira
- Jorge Fernando Ferreira da Silva
- Miguel Ribeiro Dantas de Alencar Fugita

## Algoritmos

Os cinco algoritmos pedidos no enunciado seguem o pseudocódigo da **Aula 3** (mesmos nomes de
rotinas e mesma lógica), com índices a partir de 0 em vez de 1.

| Algoritmo (nome nos CSVs) | Rotinas da aula | Melhor caso | Caso médio | Pior caso | Observação |
|---|---|---|---|---|---|
| `insertion_sort` | INSERTION-SORT | Θ(n) | Θ(n²) | Θ(n²) | melhor caso: vetor ordenado |
| `selection_sort` | SELECTION-SORT | Θ(n²) | Θ(n²) | Θ(n²) | sempre n(n−1)/2 comparações e n−1 trocas |
| `mergesort` | MERGESORT, INTERCALA | Θ(n log n) | Θ(n log n) | Θ(n log n) | vetor auxiliar B de tamanho n |
| `heapsort` | HEAPSORT, BUILD-MAX-HEAP, MAX-HEAPIFY | Θ(n log n) | Θ(n log n) | Θ(n log n) | in-place |
| `quicksort` | QUICKSORT, PARTICIONE | Θ(n log n) | Θ(n log n) | Θ(n²) | Lomuto, pivô = A[r] |
| `quicksort_aleatorio` | QUICKSORT-ALEATÓRIO, PARTICIONE-ALEATÓRIO | Θ(n log n) | Θ(n log n) | Θ(n²)* | pivô sorteado em A[p..r] |
| `quicksort_mm` (extra) | — | Θ(n log n) | Θ(n log n) | Θ(n log n) | pivô = mediana das medianas (BFPRT) |

\* O pior caso existe, mas tem probabilidade desprezível; o consumo **esperado** é Θ(n log n) para qualquer entrada.

### Detalhes de implementação

- **Selection Sort:** a troca `A[i] ↔ A[min]` é feita em toda iteração, como no slide, inclusive quando `min = i`.
- **Intercala:** copia `A[p..q]` para `B` e `A[q+1..r]` para `B` em ordem inversa, como no slide. Assim cada chamada faz exatamente r−p+1 comparações e 2(r−p+1) cópias.
- **Quicksort e Quicksort-Aleatório:** a única diferença em relação à aula é que, em vez de duas chamadas recursivas, a recursão é feita na parte menor e a maior é tratada num laço. As partições, comparações e trocas são as mesmas; só a pilha fica limitada a O(log n). Com a recursão do slide, um vetor ordenado de 100.000 elementos geraria 100.000 níveis de chamada e estouraria a pilha.
- **Quicksort MM (extra):** não faz parte da aula. Foi incluído para comparar uma escolha de pivô com garantia de pior caso O(n log n).

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

Requisitos: gcc, Python 3 com pandas, numpy e matplotlib.

```bash
make            # compila ./tempo e ./ops
make dados      # executa o experimento (alguns minutos)
make analise    # gera resultados/ e graficos/
```

Sem `make` (Linux, WSL ou Git Bash no Windows):

```bash
gcc -O2 -Wall -o tempo src/sort.c
gcc -O2 -Wall -DCONTAR -o ops src/sort.c
./tempo > dados/tempos.csv
./ops   > dados/operacoes.csv
python analise/analise.py
```

Esses comandos usam os parâmetros padrão, uma versão curta do experimento (10 repetições,
n até 1.000.000, casos O(n²) até 100.000; cerca de 20 minutos). Os dados do repositório vêm da
**coleta completa**, que leva cerca de 8 horas:

```bash
bash rodar_noite.sh
```

No Windows, gere os CSVs pelo Git Bash ou pelo `cmd`: no Windows PowerShell 5.1 o `>` grava em
UTF-16, e o pandas não lê o arquivo corretamente.

## Metodologia

- Todos os algoritmos em C, mesmo compilador e mesmas flags (`-O2`).
- Mesma entrada para todos: o vetor é gerado uma vez por repetição (gerador xorshift32 com semente fixa) e copiado para cada algoritmo.
- O pivô do Quicksort-Aleatório usa um gerador separado, reiniciado com a mesma semente em cada execução, então os resultados são reproduzíveis.
- Tempo medido com relógio monotônico de alta resolução (`clock_gettime(CLOCK_MONOTONIC)` no Linux, `QueryPerformanceCounter` no Windows). Comparações e movimentos são contados numa compilação separada (`-DCONTAR`), para não interferir no tempo.
- Tamanhos: 13 valores de 1.000 a 10.000.000 (1, 2 e 5 × 10ᵏ). Os casos O(n²) (Selection; Insertion fora do vetor ordenado; Quicksort clássico com vetor ordenado ou inverso) vão até n = 500.000. Estendê-los até 1.000.000 multiplicaria o tempo de cada execução por 4: o Selection passaria de 111 s para cerca de 7,5 min por execução, e só ele consumiria mais de 10 horas.
- Entradas: aleatória (caso médio), ordenada, inversa e quase ordenada (5% de trocas aleatórias). As entradas ordenada e inversa produzem o melhor e o pior caso de cada algoritmo.
- Repetições por configuração: 20 para o tempo e 5 para a contagem de operações, que quase não varia entre repetições. Estatísticas: média, desvio padrão, coeficiente de variação e IC 95%.
- Coleta feita com o notebook ligado na tomada e sem outros programas abertos. Em 2,4% das configurações alguma execução levou mais que o dobro da mediana (no máximo 2,6 vezes), o que indica pouca interferência externa.
- Toda execução verifica se o vetor resultante está ordenado.
- A contagem de operações é determinística e independente da máquina; o tempo foi medido em uma única máquina (abaixo).

## Ambiente de execução

| Item | Valor |
|---|---|
| CPU | Intel Core i5-4210U @ 1.70 GHz (2 núcleos, 4 threads) |
| RAM | 16 GB |
| Sistema operacional | Windows 10 Home 22H2 (build 19045) |
| Compilador | gcc 6.3.0 (MinGW.org, 32 bits) |
| Flags | -O2 -Wall |
| Coleta | 05/10/2026 22:56 a 06/10/2026 07:02 (8 h 06 min) |

## Observação sobre a escolha do pivô

O Quicksort clássico (pivô = último elemento) degrada para Θ(n²) em entradas ordenadas ou
inversas: com n = 500.000 e vetor ordenado ele levou 137 s, contra 23 ms do pivô aleatório. Na
entrada quase ordenada isso não acontece: os ~10% de elementos fora do lugar acabam virando pivô
com frequência e equilibram as partições, e o comportamento observado é O(n log n). O Quicksort-Aleatório da aula resolve isso na prática: o consumo esperado é
Θ(n log n) em qualquer entrada. A mediana das medianas vai além e **garante** que o pivô separa
pelo menos ~30% dos elementos de cada lado, eliminando o pior caso. Em contrapartida, a seleção do
pivô tem custo linear com constante alta, então ela tende a ser a mais lenta das três em entradas
aleatórias. Os dados foram gerados com poucos elementos repetidos; com muitos valores iguais, a
partição de Lomuto desbalanceia independentemente do pivô.

## Observação sobre cache (Heapsort)

Na entrada aleatória, o tempo do Heapsort cresce mais rápido que n log n a partir de
n ≈ 1.000.000 (gráfico `04_confirmacao_teorica.png`). Com 10 milhões de inteiros o vetor ocupa
40 MB, muito mais que o cache da CPU (3 MB), e o heap acessa posições distantes da memória (pai em
i, filhos em 2i+1 e 2i+2), gerando falhas de cache. O Mergesort, que percorre a memória em
sequência, não sofre esse efeito. A análise assintótica conta operações, mas não modela a
hierarquia de memória.
