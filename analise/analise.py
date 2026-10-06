"""
analise.py - Estatisticas e graficos dos experimentos de ordenacao
Uso (na raiz do repositorio):  python analise/analise.py
Requer: pandas, numpy, matplotlib
"""
import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

ALGORITMOS = ["insertion_sort", "selection_sort", "mergesort", "heapsort",
              "quicksort", "quicksort_aleatorio", "quicksort_mm"]
ENTRADAS = ["aleatorio", "ordenado", "inverso", "quase"]

NOME_ALG = {
    "insertion_sort": "Insertion Sort",
    "selection_sort": "Selection Sort",
    "mergesort": "Mergesort",
    "heapsort": "Heapsort",
    "quicksort": "Quicksort",
    "quicksort_aleatorio": "Quicksort-Aleatório",
    "quicksort_mm": "Quicksort MM (extra)",
}
NOME_ENT = {
    "aleatorio": "aleatória",
    "ordenado": "ordenada",
    "inverso": "inversa",
    "quase": "quase ordenada",
}

os.makedirs("graficos", exist_ok=True)
os.makedirs("resultados", exist_ok=True)

# ============ 1. Leitura e estatisticas ============
tempos = pd.read_csv("dados/tempos.csv")
ops = pd.read_csv("dados/operacoes.csv")


def resumir(df, coluna):
    r = (df.groupby(["algoritmo", "entrada", "n"])[coluna]
           .agg(["mean", "std", "count"])
           .reset_index())
    r["ic95"] = 1.96 * r["std"] / np.sqrt(r["count"])
    r["cv_%"] = 100 * r["std"] / r["mean"]
    return r


rt = resumir(tempos, "tempo_s")
rc = resumir(ops, "comparacoes")
rm = resumir(ops, "movimentos")

rt.to_csv("resultados/resumo_tempos.csv", index=False)
rc.to_csv("resultados/resumo_comparacoes.csv", index=False)
rm.to_csv("resultados/resumo_movimentos.csv", index=False)

# ============ 2. Modelo teorico ============
FUNCOES = {
    "n": lambda n: n,
    "n log n": lambda n: n * np.log2(n),
    "n²": lambda n: n ** 2,
}


def classe_teorica(alg, ent):
    if alg == "insertion_sort" and ent == "ordenado":
        return "n"
    if alg in ("insertion_sort", "selection_sort"):
        return "n²"
    if alg == "quicksort" and ent in ("ordenado", "inverso"):
        return "n²"
    return "n log n"   # mergesort, heapsort, quicksort (aleatorio/quase), aleatorio, mm


def dados(resumo, alg, ent):
    d = resumo[(resumo.algoritmo == alg) & (resumo.entrada == ent)]
    return d.sort_values("n")


def valor(resumo, alg, ent, n):
    d = resumo[(resumo.algoritmo == alg) & (resumo.entrada == ent) & (resumo.n == n)]
    return float(d["mean"].iloc[0]) if len(d) else float("nan")


# ============ 3. Estilo dos graficos ============
# Paleta categorica validada (daltonismo e contraste); cada algoritmo e cada
# tipo de entrada tem cor fixa em todos os graficos.
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
TINTA_FRACA = "#898781"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"
SEMI = ["Segoe UI Semibold", "DejaVu Sans"]   # titulos

COR_ALG = {
    "insertion_sort": "#2a78d6",
    "selection_sort": "#eb6834",
    "mergesort": "#1baf7a",
    "heapsort": "#eda100",
    "quicksort": "#e87ba4",
    "quicksort_aleatorio": "#008300",
    "quicksort_mm": "#4a3aa7",
}
COR_ENT = {
    "aleatorio": "#2a78d6",
    "ordenado": "#eb6834",
    "inverso": "#1baf7a",
    "quase": "#4a3aa7",
}

DPI = 200
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"],
    "font.size": 10,
    "figure.facecolor": SUPERFICIE,
    "axes.facecolor": SUPERFICIE,
    "savefig.facecolor": SUPERFICIE,
    "axes.edgecolor": EIXO,
    "axes.labelcolor": TINTA_2,
    "axes.titlecolor": TINTA,
    "xtick.color": TINTA_FRACA,
    "ytick.color": TINTA_FRACA,
    "xtick.labelcolor": TINTA_2,
    "ytick.labelcolor": TINTA_2,
    "text.color": TINTA,
    "legend.frameon": False,
    "legend.labelcolor": TINTA_2,
})


def virgula(texto):
    return texto.replace(".", ",")


def fmt_n(v, _pos=None):
    if v >= 1e6:
        return virgula(f"{v / 1e6:g} mi")
    if v >= 1e3:
        return virgula(f"{v / 1e3:g} mil")
    return f"{v:g}"


def fmt_tempo(v, _pos=None):
    if v <= 0:
        return "0"
    if v < 1e-3:
        return virgula(f"{v * 1e6:.3g} µs")
    if v < 1:
        return virgula(f"{v * 1e3:.3g} ms")
    return virgula(f"{v:.3g} s")


def estilo(ax, grade_x=True):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.grid(True, which="major", axis="y", color=GRADE, lw=0.8)
    if grade_x:
        ax.grid(True, which="major", axis="x", color=GRADE, lw=0.8)
    ax.grid(False, which="minor")
    ax.set_axisbelow(True)
    ax.tick_params(which="both", length=0, pad=6)


def eixo_n_log(ax):
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(mticker.LogLocator(base=10))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_n))
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())


def eixo_tempo_log(ax):
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(mticker.LogLocator(base=10))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_tempo))
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())


def titulo(fig, principal, sub):
    fig.text(0.01, 0.985, principal, fontsize=12, fontfamily=SEMI,
             color=TINTA, ha="left", va="top")
    fig.text(0.01, 0.94, sub, fontsize=9, color=TINTA_FRACA, ha="left", va="top")


def linha(ax, x, y, cor, rotulo=None, banda=None):
    if banda is not None:
        ax.fill_between(x, np.maximum(y - banda, y * 0.05), y + banda,
                        color=cor, alpha=0.15, lw=0)
    ax.plot(x, y, "-o", color=cor, lw=2, ms=5, mec=SUPERFICIE, mew=1.2,
            label=rotulo, zorder=3)


def pontos_e_curva(ax, d, classe, cor, rotulo, x_max):
    """Media medida como pontos soltos e, por tras, a curva c*f(n) ajustada
    por minimos quadrados (t = c*f(n), sem intercepto), desenhada continua."""
    x, y = d["n"].to_numpy(float), d["mean"].to_numpy()
    f = FUNCOES[classe]
    c = np.sum(y * f(x)) / np.sum(f(x) ** 2)
    grade = np.linspace(max(1.0, x_max / 1000), x_max, 400)
    ax.plot(grade, c * f(grade), "-", color=cor, lw=1.6, alpha=0.9, zorder=2)
    ax.plot(x, y, "o", color=cor, ms=6, mec=SUPERFICIE, mew=1.4, zorder=3)
    return plt.Line2D([], [], color=cor, lw=1.6, marker="o", ms=6, mec=SUPERFICIE,
                      mew=1.4, label=rotulo)


def rotulos_finais(ax, itens, sep_pt=12):
    """Rotulo no fim de cada linha, afastando os que colidem.
    itens: lista de (x, y, texto, cor)."""
    if not itens:
        return
    ax.figure.canvas.draw()
    tr = ax.transData
    px_por_pt = ax.figure.dpi / 72
    pos = sorted(((tr.transform((x, y))[1], x, y, t, c) for x, y, t, c in itens),
                 key=lambda p: p[0])
    novos = [pos[0][0]]
    for p in pos[1:]:
        novos.append(max(p[0], novos[-1] + sep_pt * px_por_pt))
    for (orig, x, y, t, c), novo in zip(pos, novos):
        ax.annotate(t, xy=(x, y), xytext=(8, (novo - orig) / px_por_pt),
                    textcoords="offset points", va="center", ha="left",
                    fontsize=9, color=TINTA, annotation_clip=False,
                    bbox=dict(boxstyle="square,pad=0.1", fc=SUPERFICIE, ec="none"))


def salvar(fig, nome):
    fig.savefig(f"graficos/{nome}", dpi=DPI, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


for antigo in glob.glob("graficos/*.png"):
    os.remove(antigo)

N_QUAD = int(rt[(rt.algoritmo == "selection_sort")]["n"].max())
N_MAX = int(rt["n"].max())
Y_RAZAO = 2.0          # limite do eixo y no grafico T(n)/f(n)
REP_T = int(rt["count"].max())    # repeticoes por configuracao (tempo)
RAPIDOS = ["mergesort", "heapsort", "quicksort", "quicksort_aleatorio", "quicksort_mm"]
alcas_ent = [plt.Line2D([], [], color=COR_ENT[e], lw=2, marker="o", ms=5,
                        mec=SUPERFICIE, mew=1.2) for e in ENTRADAS]

# ============ 4. Grafico 1: o abismo entre n² e n log n (escala linear) ============
# Painel esquerdo: escala completa (a distancia entre as classes).
# Painel direito: mesmo eixo de n, zoom so nos O(n log n).
fig, (ax, az) = plt.subplots(1, 2, figsize=(15, 5.8), dpi=DPI)
itens, itens_z, alcas = [], [], []
for alg in ALGORITMOS:
    d = dados(rt, alg, "aleatorio")
    d = d[d["n"] <= N_QUAD]
    if d.empty:
        continue
    x, y = d["n"].to_numpy(float), d["mean"].to_numpy()
    classe = classe_teorica(alg, "aleatorio")
    alcas.append(pontos_e_curva(ax, d, classe, COR_ALG[alg], NOME_ALG[alg], N_QUAD))
    rotulo = (x[-1], y[-1], f"{NOME_ALG[alg]}  {fmt_tempo(y[-1])}", COR_ALG[alg])
    if alg in RAPIDOS:
        pontos_e_curva(az, d, classe, COR_ALG[alg], NOME_ALG[alg], N_QUAD)
        itens_z.append(rotulo)
    else:
        itens.append(rotulo)
for eixo in (ax, az):
    estilo(eixo)
    eixo.set_xlim(0, N_QUAD * 1.02)
    eixo.set_ylim(bottom=0)
    eixo.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_n))
    eixo.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_tempo))
    eixo.set_xlabel("n (tamanho do vetor)")
ax.set_ylabel("tempo médio por execução")
ax.set_title("Escala completa", loc="left", fontsize=10, fontfamily=SEMI)
az.set_title("Zoom nos algoritmos O(n log n)", loc="left", fontsize=10,
             fontfamily=SEMI)
rotulos_finais(ax, itens)
rotulos_finais(az, itens_z)
ax.legend(handles=alcas, loc="upper left", fontsize=9)
titulo(fig, "O(n²) x O(n log n)",
       f"Entrada aleatória, escala linear. Pontos: média de {REP_T} execuções. "
       "Linhas: c·n² e c·n log n ajustadas aos pontos.")
fig.subplots_adjust(top=0.82, wspace=0.42)
salvar(fig, "01_n2_vs_nlogn.png")

# ============ 5. Grafico 2: os algoritmos O(n log n) (escala linear) ============
fig, ax = plt.subplots(figsize=(10, 5.6), dpi=DPI)
itens = []
alcas = []
for alg in RAPIDOS:
    d = dados(rt, alg, "aleatorio")
    x, y = d["n"].to_numpy(float), d["mean"].to_numpy()
    alcas.append(pontos_e_curva(ax, d, "n log n", COR_ALG[alg], NOME_ALG[alg], N_MAX))
    itens.append((x[-1], y[-1], f"{NOME_ALG[alg]}  {fmt_tempo(y[-1])}", COR_ALG[alg]))
estilo(ax)
ax.set_xlim(0, N_MAX * 1.02)
ax.set_ylim(bottom=0)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_n))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_tempo))
ax.set_xlabel("n (tamanho do vetor)")
ax.set_ylabel("tempo médio por execução")
rotulos_finais(ax, itens)
ax.legend(handles=alcas, loc="upper left", fontsize=9)
titulo(fig, "Algoritmos O(n log n)",
       f"Entrada aleatória, escala linear. Pontos: média de {REP_T} execuções. "
       "Linhas: c·n log n ajustada aos pontos (quase reta: log n cresce devagar).")
fig.subplots_adjust(top=0.84)
salvar(fig, "02_algoritmos_nlogn.png")

# ============ 6. Grafico 3: um painel por algoritmo, as 4 entradas ============
fig, eixos = plt.subplots(2, 4, figsize=(15, 7.4), dpi=DPI, sharex=True, sharey=True)
eixos = eixos.ravel()
for ax, alg in zip(eixos, ALGORITMOS):
    for ent in ENTRADAS:
        d = dados(rt, alg, ent)
        if d.empty:
            continue
        linha(ax, d["n"].to_numpy(float), d["mean"].to_numpy(), COR_ENT[ent],
              NOME_ENT[ent])
    eixo_n_log(ax)
    eixo_tempo_log(ax)
    estilo(ax)
    ax.set_title(NOME_ALG[alg], loc="left", fontsize=10, fontfamily=SEMI)
leg = eixos[-1]
leg.axis("off")
leg.legend(alcas_ent, [f"entrada {NOME_ENT[e]}" for e in ENTRADAS], loc="center left",
           fontsize=10, title="Tipo de entrada", title_fontsize=10)
for ax in eixos[3:7]:
    ax.set_xlabel("n")
    ax.xaxis.set_tick_params(labelbottom=True)
for ax in (eixos[0], eixos[4]):
    ax.set_ylabel("tempo médio")
titulo(fig, "Tempo por tipo de entrada",
       f"Escala log-log. Média de {REP_T} execuções. Casos O(n²) medidos até "
       f"n = {fmt_n(N_QUAD)}.")
fig.subplots_adjust(top=0.86, hspace=0.3, wspace=0.12)
salvar(fig, "03_tempo_por_entrada.png")

# ============ 7. Grafico 4: confirmacao da complexidade, T(n)/f(n) ============
fig, eixos = plt.subplots(2, 4, figsize=(15, 7.4), dpi=DPI, sharex=True, sharey=True)
eixos = eixos.ravel()
houve_fora = False
for ax, alg in zip(eixos, ALGORITMOS):
    ax.axhspan(0.75, 1.25, color=GRADE, alpha=0.6, lw=0, zorder=0)
    ax.axhline(1, color=EIXO, lw=1, zorder=1)
    classes = []
    for ent in ENTRADAS:
        d = dados(rt, alg, ent)
        if d.empty:
            continue
        n = d["n"].to_numpy(float)
        classe = classe_teorica(alg, ent)
        razao = d["mean"].to_numpy() / FUNCOES[classe](n)
        razao = razao / np.median(razao)
        # pontos acima do limite do eixo ficam presos no topo, marcados com ▲
        fora = razao > Y_RAZAO
        houve_fora = houve_fora or bool(fora.any())
        linha(ax, n, np.minimum(razao, Y_RAZAO), COR_ENT[ent], NOME_ENT[ent])
        ax.plot(n[fora], np.full(fora.sum(), Y_RAZAO), "^", color=COR_ENT[ent],
                ms=7, mec=SUPERFICIE, mew=1.2, zorder=4, clip_on=False)
        classes.append(classe)
    eixo_n_log(ax)
    estilo(ax)
    ax.set_ylim(0, Y_RAZAO)
    unicas = sorted(set(classes), key=lambda c: ["n", "n log n", "n²"].index(c))
    ax.set_title(f"{NOME_ALG[alg]}\n", loc="left", fontsize=10, fontfamily=SEMI)
    ax.text(0, 1.02, "f(n) = " + " ou ".join(unicas), transform=ax.transAxes,
            fontsize=9, color=TINTA_2, va="bottom")
leg = eixos[-1]
leg.axis("off")
leg.legend(alcas_ent, [f"entrada {NOME_ENT[e]}" for e in ENTRADAS], loc="upper left",
           fontsize=10, title="Tipo de entrada", title_fontsize=10)
nota = "Faixa cinza: ±25% em torno de 1."
if houve_fora:
    nota += f"\n▲ ponto acima de {Y_RAZAO:g} (fora da escala)."
leg.text(0.02, 0.0, nota, transform=leg.transAxes, fontsize=8.5, color=TINTA_FRACA,
         va="bottom")
for ax in eixos[3:7]:
    ax.set_xlabel("n")
    ax.xaxis.set_tick_params(labelbottom=True)
for ax in (eixos[0], eixos[4]):
    ax.set_ylabel("T(n) / f(n)  (normalizado)")
titulo(fig, "T(n) / f(n): curvas planas confirmam a complexidade teórica",
       "Razão entre o tempo medido e a função teórica, normalizada pela mediana.")
fig.subplots_adjust(top=0.84, hspace=0.45, wspace=0.12)
salvar(fig, "04_confirmacao_teorica.png")

# ============ 8. Grafico 5: escolha do pivo do Quicksort ============
QUICKS = ["quicksort", "quicksort_aleatorio", "quicksort_mm"]
n_q = N_QUAD
fig, ax = plt.subplots(figsize=(10, 4.6), dpi=DPI)
ys = np.arange(len(ENTRADAS))[::-1]
for y, ent in zip(ys, ENTRADAS):
    vals = [valor(rt, a, ent, n_q) for a in QUICKS]
    ax.plot([min(vals), max(vals)], [y, y], color=EIXO, lw=1.5, zorder=1)
    for a, v in zip(QUICKS, vals):
        ax.plot(v, y, "o", color=COR_ALG[a], ms=11, mec=SUPERFICIE, mew=2, zorder=3)
    i_max = int(np.argmax(vals))
    ax.annotate(fmt_tempo(vals[i_max]), xy=(vals[i_max], y), xytext=(10, 0),
                textcoords="offset points", va="center", fontsize=9, color=TINTA)
    i_min = int(np.argmin(vals))
    ax.annotate(fmt_tempo(vals[i_min]), xy=(vals[i_min], y), xytext=(-10, 0),
                textcoords="offset points", va="center", ha="right", fontsize=9,
                color=TINTA)
ax.set_yticks(ys, [f"entrada {NOME_ENT[e]}" for e in ENTRADAS])
ax.set_xscale("log")
ax.xaxis.set_major_locator(mticker.LogLocator(base=10))
ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_tempo))
ax.xaxis.set_minor_formatter(mticker.NullFormatter())
estilo(ax)
ax.grid(False, axis="y")
ax.set_xlabel(f"tempo médio com n = {fmt_n(n_q)} (escala log)")
alcas_q = [plt.Line2D([], [], color=COR_ALG[a], lw=0, marker="o", ms=9,
                      mec=SUPERFICIE, mew=1.5) for a in QUICKS]
ax.legend(alcas_q, ["pivô = último elemento (aula)", "pivô aleatório (aula)",
                    "pivô = mediana das medianas (extra)"],
          loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=9)
ax.margins(x=0.12)
titulo(fig, "Quicksort: efeito da escolha do pivô",
       f"n = {fmt_n(n_q)}, média de {REP_T} execuções. Escala logarítmica.")
fig.subplots_adjust(top=0.8)
salvar(fig, "05_quicksort_pivo.png")

# ============ 9. Grafico 6: contagens normalizadas x constantes teoricas ============
fig, eixos = plt.subplots(2, 2, figsize=(14, 8.4), dpi=DPI, sharex="col")
paineis = [
    (eixos[0, 0], rc, RAPIDOS, "n log n", "comparações / (n log₂ n)"),
    (eixos[0, 1], rc, ["insertion_sort", "selection_sort"], "n²/2",
     "comparações / (n²/2)"),
    (eixos[1, 0], rm, RAPIDOS, "n log n", "movimentos / (n log₂ n)"),
    (eixos[1, 1], rm, ["insertion_sort", "selection_sort"], "n²/2",
     "movimentos / (n²/2)"),
]
for ax, resumo, algs, f, rotulo_y in paineis:
    itens = []
    for alg in algs:
        d = dados(resumo, alg, "aleatorio")
        n = d["n"].to_numpy(float)
        div = n * np.log2(n) if f == "n log n" else n ** 2 / 2
        y = d["mean"].to_numpy() / div
        linha(ax, n, y, COR_ALG[alg], NOME_ALG[alg])
        itens.append((n[-1], y[-1], f"{NOME_ALG[alg]}  {virgula(f'{y[-1]:.2f}')}",
                      COR_ALG[alg]))
    eixo_n_log(ax)
    estilo(ax)
    ax.set_ylim(bottom=0)
    ax.set_ylabel(rotulo_y)
    rotulos_finais(ax, itens)
eixos[0, 0].axhline(2 * np.log(2), color=TINTA_FRACA, lw=1, ls=(0, (4, 3)), zorder=1)
eixos[0, 0].text(1.02e3, 2 * np.log(2) + 0.06,
                 "teoria do Quicksort médio: 2 ln 2 ≈ 1,39",
                 fontsize=8.5, color=TINTA_2)
eixos[0, 1].axhline(0.5, color=TINTA_FRACA, lw=1, ls=(0, (4, 3)), zorder=1)
eixos[0, 1].text(1.02e3, 0.53, "teoria do Insertion médio: n²/4", fontsize=8.5,
                 color=TINTA_2)
eixos[0, 0].set_title("Algoritmos O(n log n)", loc="left", fontsize=10,
                      fontfamily=SEMI)
eixos[0, 1].set_title("Algoritmos O(n²)", loc="left", fontsize=10, fontfamily=SEMI)
for ax in eixos[1]:
    ax.set_xlabel("n")
titulo(fig, "Operações divididas pela função de crescimento",
       "Entrada aleatória. Cada curva converge para a sua constante.")
fig.subplots_adjust(top=0.88, hspace=0.18, wspace=0.42)
salvar(fig, "06_operacoes_normalizadas.png")

# ============ 10. Expoente empirico (inclinacao no log-log) ============
linhas = []
for (alg, ent), d in rt.groupby(["algoritmo", "entrada"]):
    d = d[d["n"] >= 5000].sort_values("n")   # n pequeno tem muito ruido
    if len(d) < 3:
        continue
    a, _ = np.polyfit(np.log10(d["n"]), np.log10(d["mean"]), 1)
    linhas.append({"algoritmo": alg, "entrada": ent,
                   "expoente_empirico": round(a, 2),
                   "classe_teorica": classe_teorica(alg, ent)})
expo = pd.DataFrame(linhas)
expo.to_csv("resultados/expoentes.csv", index=False)
print("\nExpoente empírico (T ~ n^a):")
print(expo.pivot(index="algoritmo", columns="entrada", values="expoente_empirico"))

# ============ 11. Tabela compacta para os slides (ms) ============
tab = rt[(rt.entrada == "aleatorio") & (rt.n.isin([10000, 50000, 100000]))].copy()
tab["texto"] = ((tab["mean"] * 1000).map("{:.2f}".format) + " ± "
                + (tab["std"] * 1000).map("{:.2f}".format))
tab = tab.pivot(index="algoritmo", columns="n", values="texto")
tab.to_csv("resultados/tabela_slides_ms.csv")
print("\nTempo médio ± desvio padrão (ms), entrada aleatória:")
print(tab)

# ============ 12. Custo da escolha do pivo na entrada aleatoria ============
pv = rt[rt.entrada == "aleatorio"].pivot(index="n", columns="algoritmo", values="mean")
fator = pd.DataFrame({
    "aleatorio/quicksort": pv["quicksort_aleatorio"] / pv["quicksort"],
    "mm/quicksort": pv["quicksort_mm"] / pv["quicksort"],
}).round(2)
fator.to_csv("resultados/fator_pivo.csv")
print("\nTempo relativo ao quicksort clássico (entrada aleatória):")
print(fator)

# ============ 13. Verificacoes exatas com a teoria ============
sel = rc[rc.algoritmo == "selection_sort"]
ok = (sel["mean"] == sel["n"] * (sel["n"] - 1) / 2).all()
print(f"\nSelection faz exatamente n(n-1)/2 comparações em toda entrada: {ok}")
sel = rm[rm.algoritmo == "selection_sort"]
ok = (sel["mean"] == sel["n"] - 1).all()
print(f"Selection faz exatamente n-1 trocas em toda entrada: {ok}")
ins = rc[(rc.algoritmo == "insertion_sort") & (rc.entrada == "ordenado")]
ok = (ins["mean"] == ins["n"] - 1).all()
print(f"Insertion (melhor caso) faz exatamente n-1 comparações: {ok}")
ins = rm[(rm.algoritmo == "insertion_sort") & (rm.entrada == "ordenado")]
ok = (ins["mean"] == 0).all()
print(f"Insertion (melhor caso) faz zero deslocamentos: {ok}")
# Intercala da aula: r-p+1 comparações e 2(r-p+1) cópias por chamada,
# logo o total de comparações não depende da entrada e movimentos = 2x
mc = rc[rc.algoritmo == "mergesort"].set_index(["entrada", "n"])["mean"]
mm = rm[rm.algoritmo == "mergesort"].set_index(["entrada", "n"])["mean"]
ok = (mm == 2 * mc).all()
print(f"Mergesort: movimentos = 2 x comparações em toda entrada: {ok}")
ok = (mc.groupby("n").nunique() == 1).all()
print(f"Mergesort: nº de comparações independe do tipo de entrada: {ok}")
