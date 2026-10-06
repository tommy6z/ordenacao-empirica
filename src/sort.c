/*
 * sort.c - Analise empirica de algoritmos de ordenacao
 *
 * Os algoritmos seguem o pseudocodigo da Aula 3 (Analise de Algoritmos,
 * Prof. Daniel Pedronette), com indices a partir de 0 em vez de 1.
 *
 * Compilar (duas versoes do mesmo codigo):
 *   gcc -O2 -Wall -o tempo src/sort.c             -> mede tempo
 *   gcc -O2 -Wall -DCONTAR -o ops src/sort.c      -> conta operacoes
 *
 * Executar (na raiz do repositorio):
 *   ./tempo > dados/tempos.csv
 *   ./ops   > dados/operacoes.csv
 *
 * Os parametros do experimento podem ser trocados na compilacao, ex.:
 *   gcc -O2 -Wall -DREPETICOES=30 -DN_MAX=10000000 -DN_MAX_QUAD=200000 ...
 *
 * Medidas:
 *   comparacoes = comparacoes entre elementos do vetor
 *   movimentos  = trocas (1 por troca) + deslocamentos/copias de elementos
 */

#define _POSIX_C_SOURCE 199309L
#ifdef _WIN32
#define _WIN32_WINNT 0x0501      /* SetThreadExecutionState */
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#endif

/* ================= Parametros do experimento ================= */

#ifndef REPETICOES
#define REPETICOES 10
#endif

#ifndef N_MAX
#define N_MAX      1000000        /* maior n medido */
#endif

#ifndef N_MAX_QUAD
#define N_MAX_QUAD 100000         /* limite de n para casos O(n^2) */
#endif

/* Tamanhos acima de N_MAX sao ignorados */
static const int TAMANHOS[] =
{
    1000, 2000, 5000, 10000, 20000, 50000,
    100000, 200000, 500000, 1000000,
    2000000, 5000000, 10000000
};

#define NUM_TAMANHOS ((int)(sizeof(TAMANHOS) / sizeof(TAMANHOS[0])))

/* ================= Contadores ================= */

static unsigned long long comparacoes = 0;
static unsigned long long movimentos = 0;

#ifdef CONTAR
#define CONTA_CMP() (comparacoes++)
#define CONTA_MOV() (movimentos++)
#else
#define CONTA_CMP() ((void)0)
#define CONTA_MOV() ((void)0)
#endif

#define MAIOR(a, b)       (CONTA_CMP(), (a) > (b))
#define MENOR(a, b)       (CONTA_CMP(), (a) < (b))
#define MENOR_IGUAL(a, b) (CONTA_CMP(), (a) <= (b))

static void troca(int *a, int *b)
{
    int tmp = *a;
    *a = *b;
    *b = tmp;
    CONTA_MOV();
}

/* ================= Gerador de numeros (xorshift32) =================
 * Gerador proprio para que a sequencia seja identica em qualquer
 * sistema operacional/compilador (rand() varia entre plataformas).
 * Dois estados independentes: um gera as entradas e outro sorteia o
 * pivo do Quicksort-Aleatorio, para um nao interferir no outro. */

static uint32_t estado = 1;          /* gerador das entradas */
static uint32_t estado_pivo = 1;     /* gerador do pivo aleatorio */

static uint32_t xorshift32(uint32_t *s)
{
    *s ^= *s << 13;
    *s ^= *s >> 17;
    *s ^= *s << 5;
    return *s;
}

static uint32_t aleatorio(void)
{
    return xorshift32(&estado);
}

/* ================= Tipos de entrada ================= */

enum
{
    ALEATORIO,
    ORDENADO,
    INVERSO,
    QUASE,
    NUM_ENTRADAS
};

static const char *NOME_ENTRADA[] =
{
    "aleatorio", "ordenado", "inverso", "quase"
};

static void gera_entrada(int *v, int n, int tipo, uint32_t semente)
{
    if (semente == 0)
    {
        semente = 1;
    }
    estado = semente;

    if (tipo == ALEATORIO)
    {
        for (int i = 0; i < n; i++)
        {
            v[i] = (int)(aleatorio() >> 1);
        }
    }
    else if (tipo == INVERSO)
    {
        for (int i = 0; i < n; i++)
        {
            v[i] = n - i;
        }
    }
    else
    {
        for (int i = 0; i < n; i++)
        {
            v[i] = i;
        }

        if (tipo == QUASE)
        {
            /* 5% de trocas aleatorias sobre o vetor ordenado */
            for (int k = 0; k < n / 20; k++)
            {
                int i = (int)(aleatorio() % (uint32_t)n);
                int j = (int)(aleatorio() % (uint32_t)n);
                int tmp = v[i];
                v[i] = v[j];
                v[j] = tmp;
            }
        }
    }
}

/* ================= Insertion Sort =================
 * INSERTION-SORT(A, n) da aula. */

void insertion_sort(int *v, int n)
{
    for (int j = 1; j < n; j++)
    {
        int chave = v[j];
        int i = j - 1;

        while (i >= 0 && MAIOR(v[i], chave))
        {
            v[i + 1] = v[i];
            CONTA_MOV();
            i--;
        }
        v[i + 1] = chave;
    }
}

/* ================= Selection Sort =================
 * SELECTION-SORT(A, n) da aula: a troca A[i] <-> A[min] e feita em
 * toda iteracao (mesmo com min == i), totalizando n-1 trocas. */

void selection_sort(int *v, int n)
{
    for (int i = 0; i < n - 1; i++)
    {
        int min = i;

        for (int j = i + 1; j < n; j++)
        {
            if (MENOR(v[j], v[min]))
            {
                min = j;
            }
        }

        troca(&v[i], &v[min]);
    }
}

/* ================= Mergesort =================
 * MERGESORT(A, p, r) e INTERCALA(A, p, q, r) da aula. A intercala copia
 * A[p..q] para B[p..q] e A[q+1..r] para B[q+1..r] em ordem INVERSA;
 * assim o maior elemento de cada metade serve de sentinela e o laco
 * principal faz exatamente r-p+1 comparacoes, sem testar limites. */

static void intercala(int *A, int *B, int p, int q, int r)
{
    for (int i = p; i <= q; i++)
    {
        B[i] = A[i];
        CONTA_MOV();
    }

    for (int j = q + 1; j <= r; j++)
    {
        B[r + q + 1 - j] = A[j];
        CONTA_MOV();
    }

    int i = p;
    int j = r;

    for (int k = p; k <= r; k++)
    {
        if (MENOR_IGUAL(B[i], B[j]))
        {
            A[k] = B[i];
            i++;
        }
        else
        {
            A[k] = B[j];
            j--;
        }
        CONTA_MOV();
    }
}

static void mergesort_rec(int *A, int *B, int p, int r)
{
    if (p < r)
    {
        int q = p + (r - p) / 2;

        mergesort_rec(A, B, p, q);
        mergesort_rec(A, B, q + 1, r);
        intercala(A, B, p, q, r);
    }
}

void mergesort(int *v, int n)
{
    int *B = malloc((size_t)n * sizeof(int));

    if (B == NULL)
    {
        fprintf(stderr, "Erro de memoria no mergesort\n");
        exit(1);
    }

    mergesort_rec(v, B, 0, n - 1);
    free(B);
}

/* ================= Heapsort =================
 * MAX-HEAPIFY, BUILD-MAX-HEAP e HEAPSORT da aula. Com indices a partir
 * de 0, os filhos de i ficam em 2i+1 e 2i+2 (na aula: 2i e 2i+1). */

static void max_heapify(int *A, int n, int i)
{
    int e = 2 * i + 1;
    int d = 2 * i + 2;
    int maior;

    if (e < n && MAIOR(A[e], A[i]))
    {
        maior = e;
    }
    else
    {
        maior = i;
    }

    if (d < n && MAIOR(A[d], A[maior]))
    {
        maior = d;
    }

    if (maior != i)
    {
        troca(&A[i], &A[maior]);
        max_heapify(A, n, maior);
    }
}

static void build_max_heap(int *A, int n)
{
    for (int i = n / 2 - 1; i >= 0; i--)
    {
        max_heapify(A, n, i);
    }
}

void heapsort(int *v, int n)
{
    build_max_heap(v, n);
    int m = n;

    for (int i = n - 1; i > 0; i--)
    {
        troca(&v[0], &v[i]);
        m--;
        max_heapify(v, m, 0);
    }
}

/* ================= Quicksort =================
 * PARTICIONE(A, p, r) e QUICKSORT(A, p, r) da aula (Lomuto, pivo A[r]).
 * Pior caso O(n^2) em vetores ordenados ou inversos (na entrada quase
 * ordenada os elementos fora do lugar viram pivos razoaveis e o
 * comportamento observado e O(n log n)).
 * Unica diferenca para a aula: em vez de duas chamadas recursivas, a
 * recursao e feita na menor parte e a maior e tratada no laco. As
 * particoes, comparacoes e trocas sao exatamente as mesmas; so a pilha
 * fica limitada a O(log n) (com n = 100.000 ordenado, a versao da aula
 * teria 100.000 niveis de recursao e estouraria a pilha). */

static int particione(int *A, int p, int r)
{
    int x = A[r];
    int i = p - 1;

    for (int j = p; j < r; j++)
    {
        if (MENOR_IGUAL(A[j], x))
        {
            i++;
            troca(&A[i], &A[j]);
        }
    }

    troca(&A[i + 1], &A[r]);
    return i + 1;
}

static void quicksort_rec(int *A, int p, int r)
{
    while (p < r)
    {
        int q = particione(A, p, r);

        if (q - p < r - q)
        {
            quicksort_rec(A, p, q - 1);
            p = q + 1;
        }
        else
        {
            quicksort_rec(A, q + 1, r);
            r = q - 1;
        }
    }
}

void quicksort(int *v, int n)
{
    quicksort_rec(v, 0, n - 1);
}

/* ================= Quicksort-Aleatorio =================
 * PARTICIONE-ALEATORIO e QUICKSORT-ALEATORIO da aula: sorteia um indice
 * em A[p..r], troca com A[r] e chama PARTICIONE. Caso medio O(n log n)
 * em qualquer tipo de entrada. Mesma estrutura de recursao do quicksort. */

static int particione_aleatorio(int *A, int p, int r)
{
    int i = p + (int)(xorshift32(&estado_pivo) % (uint32_t)(r - p + 1));
    troca(&A[i], &A[r]);
    return particione(A, p, r);
}

static void quicksort_aleatorio_rec(int *A, int p, int r)
{
    while (p < r)
    {
        int q = particione_aleatorio(A, p, r);

        if (q - p < r - q)
        {
            quicksort_aleatorio_rec(A, p, q - 1);
            p = q + 1;
        }
        else
        {
            quicksort_aleatorio_rec(A, q + 1, r);
            r = q - 1;
        }
    }
}

void quicksort_aleatorio(int *v, int n)
{
    quicksort_aleatorio_rec(v, 0, n - 1);
}

/* ================= Quicksort com Mediana das Medianas (extra) =================
 * Nao faz parte da Aula 3; incluido para comparacao.
 * Pivo escolhido pelo algoritmo BFPRT (Blum, Floyd, Pratt, Rivest,
 * Tarjan, 1973):
 *   1. divide o subvetor em grupos de 5 elementos;
 *   2. ordena cada grupo e pega sua mediana;
 *   3. encontra RECURSIVAMENTE a mediana dessas medianas (selecao em O(n)).
 * O pivo resultante fica garantidamente entre ~30% e ~70% dos elementos,
 * entao a particao nunca e degenerada: pior caso O(n log n).
 * Custo: constante bem maior que a do quicksort classico. */

static void ordena_pequeno(int *v, int ini, int fim)
{
    for (int i = ini + 1; i <= fim; i++)
    {
        int chave = v[i];
        int j = i - 1;

        while (j >= ini && MAIOR(v[j], chave))
        {
            v[j + 1] = v[j];
            CONTA_MOV();
            j--;
        }
        v[j + 1] = chave;
    }
}

static int seleciona(int *v, int ini, int fim, int k);

/* Retorna o indice do pivo (mediana das medianas) em v[ini..fim] */
static int pivo_mm(int *v, int ini, int fim)
{
    int n = fim - ini + 1;

    if (n <= 5)
    {
        ordena_pequeno(v, ini, fim);
        return ini + (n - 1) / 2;
    }

    /* Mediana de cada grupo de 5 e levada para o inicio do subvetor */
    int m = ini;

    for (int i = ini; i <= fim; i += 5)
    {
        int f = i + 4;

        if (f > fim)
        {
            f = fim;
        }

        ordena_pequeno(v, i, f);
        troca(&v[m], &v[i + (f - i) / 2]);
        m++;
    }

    /* Mediana das medianas, que agora estao em v[ini..m-1] */
    int qtd = m - ini;
    return seleciona(v, ini, m - 1, ini + (qtd - 1) / 2);
}

/* Selecao linear: posiciona em v[k] o elemento que estaria
 * nessa posicao se v[ini..fim] estivesse ordenado */
static int seleciona(int *v, int ini, int fim, int k)
{
    while (ini < fim)
    {
        int idx = pivo_mm(v, ini, fim);
        troca(&v[idx], &v[fim]);
        int p = particione(v, ini, fim);

        if (k == p)
        {
            return p;
        }
        else if (k < p)
        {
            fim = p - 1;
        }
        else
        {
            ini = p + 1;
        }
    }

    return ini;
}

static void quicksort_mm_rec(int *v, int ini, int fim)
{
    while (fim - ini + 1 > 5)
    {
        int idx = pivo_mm(v, ini, fim);
        troca(&v[idx], &v[fim]);
        int p = particione(v, ini, fim);

        if (p - ini < fim - p)
        {
            quicksort_mm_rec(v, ini, p - 1);
            ini = p + 1;
        }
        else
        {
            quicksort_mm_rec(v, p + 1, fim);
            fim = p - 1;
        }
    }

    if (ini < fim)
    {
        ordena_pequeno(v, ini, fim);
    }
}

void quicksort_mm(int *v, int n)
{
    quicksort_mm_rec(v, 0, n - 1);
}

/* ================= Tabela de algoritmos ================= */

typedef void (*FuncaoOrdena)(int *, int);

enum
{
    INSERTION,
    SELECTION,
    MERGE,
    HEAP,
    QUICK,
    QUICK_ALEATORIO,
    QUICK_MM,
    NUM_ALGORITMOS
};

static const char *NOME_ALGORITMO[] =
{
    "insertion_sort", "selection_sort", "mergesort", "heapsort",
    "quicksort", "quicksort_aleatorio", "quicksort_mm"
};

static const FuncaoOrdena ALGORITMO[] =
{
    insertion_sort, selection_sort, mergesort, heapsort,
    quicksort, quicksort_aleatorio, quicksort_mm
};

/* ================= Utilitarios ================= */

/* Relogio monotonico de alta resolucao: clock_gettime no Linux,
 * QueryPerformanceCounter no Windows (MinGW nao tem clock_gettime) */
static double agora(void)
{
#ifdef _WIN32
    LARGE_INTEGER freq, cont;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&cont);
    return (double)cont.QuadPart / (double)freq.QuadPart;
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
#endif
}

static int esta_ordenado(const int *v, int n)
{
    for (int i = 1; i < n; i++)
    {
        if (v[i - 1] > v[i])
        {
            return 0;
        }
    }
    return 1;
}

/* Casos O(n^2) so rodam ate N_MAX_QUAD para o experimento terminar */
static int permitido(int alg, int tipo, int n)
{
    int quadratico = (alg == SELECTION)
                  || (alg == INSERTION && tipo != ORDENADO)
                  || (alg == QUICK && (tipo == ORDENADO || tipo == INVERSO));

    return !quadratico || n <= N_MAX_QUAD;
}

/* ================= Programa principal ================= */

int main(void)
{
    int *base = malloc((size_t)N_MAX * sizeof(int));
    int *v = malloc((size_t)N_MAX * sizeof(int));

    if (base == NULL || v == NULL)
    {
        fprintf(stderr, "Erro de memoria\n");
        return 1;
    }

#ifdef _WIN32
    /* Pede ao Windows para nao suspender enquanto a coleta roda
     * (a tela pode apagar normalmente) */
    SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED);
#endif

#ifdef CONTAR
    printf("algoritmo,entrada,n,rep,comparacoes,movimentos\n");
#else
    printf("algoritmo,entrada,n,rep,tempo_s\n");
#endif

    double inicio = agora();

    for (int e = 0; e < NUM_ENTRADAS; e++)
    {
        for (int s = 0; s < NUM_TAMANHOS; s++)
        {
            int n = TAMANHOS[s];

            if (n > N_MAX)
            {
                continue;
            }

            fprintf(stderr, "[%6.0f s] entrada=%s n=%d\n",
                    agora() - inicio, NOME_ENTRADA[e], n);

            for (int r = 0; r < REPETICOES; r++)
            {
                /* Mesma semente => mesma entrada para todos os algoritmos */
                uint32_t semente = 12345u
                                 + 1000003u * (uint32_t)e
                                 + 7919u * (uint32_t)n
                                 + (uint32_t)r;

                gera_entrada(base, n, e, semente);

                for (int a = 0; a < NUM_ALGORITMOS; a++)
                {
                    if (!permitido(a, e, n))
                    {
                        continue;
                    }

                    memcpy(v, base, (size_t)n * sizeof(int));
                    comparacoes = 0;
                    movimentos = 0;

                    /* Pivos sorteados reproduziveis (mesma semente => mesmos pivos) */
                    estado_pivo = semente ^ 0x9E3779B9u;
                    if (estado_pivo == 0)
                    {
                        estado_pivo = 1;
                    }

                    double t0 = agora();
                    ALGORITMO[a](v, n);
                    double t1 = agora();

                    if (!esta_ordenado(v, n))
                    {
                        fprintf(stderr, "ERRO: %s nao ordenou (%s, n=%d)\n",
                                NOME_ALGORITMO[a], NOME_ENTRADA[e], n);
                        return 1;
                    }

#ifdef CONTAR
                    (void)t0;
                    (void)t1;
                    printf("%s,%s,%d,%d,%llu,%llu\n",
                           NOME_ALGORITMO[a], NOME_ENTRADA[e], n, r,
                           comparacoes, movimentos);
#else
                    printf("%s,%s,%d,%d,%.9f\n",
                           NOME_ALGORITMO[a], NOME_ENTRADA[e], n, r,
                           t1 - t0);
#endif
                    /* Grava cada linha na hora: se a coleta for interrompida,
                     * o que ja foi medido fica salvo */
                    fflush(stdout);
                }
            }
        }
    }

    free(base);
    free(v);
    return 0;
}
