/*
 * sort.c - Analise empirica de algoritmos de ordenacao
 *
 * Compilar (duas versoes do mesmo codigo):
 *   gcc -O2 -Wall -o tempo src/sort.c             -> mede tempo
 *   gcc -O2 -Wall -DCONTAR -o ops src/sort.c      -> conta operacoes
 *
 * Executar (na raiz do repositorio):
 *   ./tempo > dados/tempos.csv
 *   ./ops   > dados/operacoes.csv
 *
 * Medidas:
 *   comparacoes = comparacoes entre elementos do vetor
 *   movimentos  = trocas (1 por troca) + deslocamentos/copias de elementos
 */

#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

/* ================= Parametros do experimento ================= */

#define REPETICOES 10
#define N_MAX      1000000
#define N_MAX_QUAD 50000          /* limite de n para casos O(n^2) */

static const int TAMANHOS[] =
{
    1000, 2000, 5000, 10000, 20000, 50000,
    100000, 200000, 500000, 1000000
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
 * sistema operacional/compilador (rand() varia entre plataformas). */

static uint32_t estado = 1;

static uint32_t aleatorio(void)
{
    estado ^= estado << 13;
    estado ^= estado >> 17;
    estado ^= estado << 5;
    return estado;
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

/* ================= Insertion Sort ================= */

void insertion_sort(int *v, int n)
{
    for (int i = 1; i < n; i++)
    {
        int chave = v[i];
        int j = i - 1;

        while (j >= 0 && MAIOR(v[j], chave))
        {
            v[j + 1] = v[j];
            CONTA_MOV();
            j--;
        }
        v[j + 1] = chave;
    }
}

/* ================= Selection Sort ================= */

void selection_sort(int *v, int n)
{
    for (int i = 0; i < n - 1; i++)
    {
        int min = i;

        for (int j = i + 1; j < n; j++)
        {
            if (MAIOR(v[min], v[j]))
            {
                min = j;
            }
        }

        if (min != i)
        {
            troca(&v[i], &v[min]);
        }
    }
}

/* ================= Merge Sort ================= */

static void intercala(int *v, int *aux, int ini, int meio, int fim)
{
    int i = ini;
    int j = meio + 1;
    int k = ini;

    while (i <= meio && j <= fim)
    {
        if (MENOR_IGUAL(v[i], v[j]))
        {
            aux[k++] = v[i++];
        }
        else
        {
            aux[k++] = v[j++];
        }
        CONTA_MOV();
    }

    while (i <= meio)
    {
        aux[k++] = v[i++];
        CONTA_MOV();
    }

    while (j <= fim)
    {
        aux[k++] = v[j++];
        CONTA_MOV();
    }

    for (k = ini; k <= fim; k++)
    {
        v[k] = aux[k];
    }
}

static void merge_rec(int *v, int *aux, int ini, int fim)
{
    if (ini >= fim)
    {
        return;
    }

    int meio = ini + (fim - ini) / 2;

    merge_rec(v, aux, ini, meio);
    merge_rec(v, aux, meio + 1, fim);
    intercala(v, aux, ini, meio, fim);
}

void merge_sort(int *v, int n)
{
    int *aux = malloc((size_t)n * sizeof(int));

    if (aux == NULL)
    {
        fprintf(stderr, "Erro de memoria no merge sort\n");
        exit(1);
    }

    merge_rec(v, aux, 0, n - 1);
    free(aux);
}

/* ================= Heap Sort ================= */

static void desce(int *v, int n, int i)
{
    while (1)
    {
        int maior = i;
        int esq = 2 * i + 1;
        int dir = 2 * i + 2;

        if (esq < n && MAIOR(v[esq], v[maior]))
        {
            maior = esq;
        }

        if (dir < n && MAIOR(v[dir], v[maior]))
        {
            maior = dir;
        }

        if (maior == i)
        {
            break;
        }

        troca(&v[i], &v[maior]);
        i = maior;
    }
}

void heap_sort(int *v, int n)
{
    for (int i = n / 2 - 1; i >= 0; i--)
    {
        desce(v, n, i);
    }

    for (int i = n - 1; i > 0; i--)
    {
        troca(&v[0], &v[i]);
        desce(v, i, 0);
    }
}

/* ================= Quick Sort (classico) =================
 * Particao de Lomuto, pivo = ultimo elemento.
 * Pior caso O(n^2) em vetores ordenados/inversos/quase ordenados.
 * A recursao e feita sempre na menor parte, o que limita a pilha
 * a O(log n) mesmo no pior caso (evita stack overflow). */

static int particiona(int *v, int ini, int fim)
{
    int pivo = v[fim];
    int i = ini - 1;

    for (int j = ini; j < fim; j++)
    {
        if (MENOR_IGUAL(v[j], pivo))
        {
            i++;
            troca(&v[i], &v[j]);
        }
    }

    troca(&v[i + 1], &v[fim]);
    return i + 1;
}

static void quick_rec(int *v, int ini, int fim)
{
    while (ini < fim)
    {
        int p = particiona(v, ini, fim);

        if (p - ini < fim - p)
        {
            quick_rec(v, ini, p - 1);
            ini = p + 1;
        }
        else
        {
            quick_rec(v, p + 1, fim);
            fim = p - 1;
        }
    }
}

void quick_sort(int *v, int n)
{
    quick_rec(v, 0, n - 1);
}

/* ================= Quick Sort com Mediana das Medianas =================
 * Pivo escolhido pelo algoritmo BFPRT (Blum, Floyd, Pratt, Rivest,
 * Tarjan, 1973):
 *   1. divide o subvetor em grupos de 5 elementos;
 *   2. ordena cada grupo e pega sua mediana;
 *   3. encontra RECURSIVAMENTE a mediana dessas medianas (selecao em O(n)).
 * O pivo resultante fica garantidamente entre ~30% e ~70% dos elementos,
 * entao a particao nunca e degenerada: pior caso O(n log n).
 * Custo: constante bem maior que a do quick classico. */

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
        int p = particiona(v, ini, fim);

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

static void quick_mm_rec(int *v, int ini, int fim)
{
    while (fim - ini + 1 > 5)
    {
        int idx = pivo_mm(v, ini, fim);
        troca(&v[idx], &v[fim]);
        int p = particiona(v, ini, fim);

        if (p - ini < fim - p)
        {
            quick_mm_rec(v, ini, p - 1);
            ini = p + 1;
        }
        else
        {
            quick_mm_rec(v, p + 1, fim);
            fim = p - 1;
        }
    }

    if (ini < fim)
    {
        ordena_pequeno(v, ini, fim);
    }
}

void quick_mm_sort(int *v, int n)
{
    quick_mm_rec(v, 0, n - 1);
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
    QUICK_MM,
    NUM_ALGORITMOS
};

static const char *NOME_ALGORITMO[] =
{
    "insertion", "selection", "merge", "heap", "quick", "quick_mm"
};

static const FuncaoOrdena ALGORITMO[] =
{
    insertion_sort, selection_sort, merge_sort, heap_sort,
    quick_sort, quick_mm_sort
};

/* ================= Utilitarios ================= */

static double agora(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
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
                  || (alg == QUICK && tipo != ALEATORIO);

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

#ifdef CONTAR
    printf("algoritmo,entrada,n,rep,comparacoes,movimentos\n");
#else
    printf("algoritmo,entrada,n,rep,tempo_s\n");
#endif

    for (int e = 0; e < NUM_ENTRADAS; e++)
    {
        for (int s = 0; s < NUM_TAMANHOS; s++)
        {
            int n = TAMANHOS[s];
            fprintf(stderr, "entrada=%s n=%d\n", NOME_ENTRADA[e], n);

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
                }
            }
        }
    }

    free(base);
    free(v);
    return 0;
}
