"""
analise.py - Estatisticas e graficos dos experimentos de ordenacao
Uso (na raiz do repositorio):  python analise/analise.py
Requer: pandas, numpy, matplotlib
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ALGORITMOS = ["insertion", "selection", "merge", "heap", "quick", "quick_mm"]
ENTRADAS = ["aleatorio", "ordenado", "inverso", "quase"]

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
    if alg == "insertion" and ent == "ordenado":
        return "n"
    if alg in ("insertion", "selection"):
        return "n²"
    if alg == "quick" and ent != "aleatorio":
        return "n²"
    return "n log n"          # merge, heap, quick (aleatorio), quick_mm


def ajusta_constante(t, f):
    # minimos quadrados para t = c * f(n)
    return np.sum(t * f) / np.sum(f * f)


def dados(resumo, alg, ent):
    d = resumo[(resumo.algoritmo == alg) & (resumo.entrada == ent)]
    return d.sort_values("n")


# ============ 3. Tempo: todos os algoritmos por entrada ============
for ent in ENTRADAS:
    fig, ax = plt.subplots(figsize=(8, 5))
    for alg in ALGORITMOS:
        d = dados(rt, alg, ent)
        if d.empty:
            continue
        ax.errorbar(d["n"], d["mean"], yerr=d["std"],
                    fmt="o-", capsize=3, label=alg)
    ax.set(xscale="log", yscale="log", xlabel="n (tamanho da entrada)",
           ylabel="tempo médio (s)", title=f"Tempo de execução - entrada {ent}")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.savefig(f"graficos/tempo_{ent}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

# ============ 4. Medido x teorico, um grafico por algoritmo ============
for alg in ALGORITMOS:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    for ent in ENTRADAS:
        d = dados(rt, alg, ent)
        if d.empty:
            continue
        n = d["n"].to_numpy(dtype=float)
        t = d["mean"].to_numpy()
        classe = classe_teorica(alg, ent)
        f = FUNCOES[classe](n)
        c = ajusta_constante(t, f)

        pts = ax1.errorbar(n, t, yerr=d["std"].to_numpy(), fmt="o",
                           capsize=3, label=f"{ent} (medido)")
        cor = pts[0].get_color()
        ax1.plot(n, c * f, "--", color=cor, label=f"{ent}: c·{classe}")

        razao = (t / f) / (t[-1] / f[-1])
        ax2.plot(n, razao, "o-", color=cor, label=f"{ent} [{classe}]")

    ax1.set(xscale="log", yscale="log", xlabel="n", ylabel="tempo (s)",
            title=f"{alg}: medido x curva teórica ajustada")
    ax2.axhline(1, color="gray", lw=0.8)
    ax2.set(xscale="log", ylim=(0, 3), xlabel="n",
            ylabel="T(n) / f(n)  (normalizado)",
            title="Razão constante ⇒ complexidade confirmada")
    for ax in (ax1, ax2):
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8)
    fig.savefig(f"graficos/teoria_{alg}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

# ============ 5. Quick classico x Quick mediana das medianas ============
fig, axes = plt.subplots(1, 4, figsize=(18, 4.5), sharey=True)
for ax, ent in zip(axes, ENTRADAS):
    for alg in ["quick", "quick_mm"]:
        d = dados(rt, alg, ent)
        if d.empty:
            continue
        ax.errorbar(d["n"], d["mean"], yerr=d["std"],
                    fmt="o-", capsize=3, label=alg)
    ax.set(xscale="log", yscale="log", xlabel="n", title=f"entrada {ent}")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
axes[0].set_ylabel("tempo médio (s)")
fig.suptitle("Quick Sort: pivô = último elemento  x  pivô = mediana das medianas")
fig.savefig("graficos/quick_vs_quick_mm.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ============ 6. Comparacoes e movimentos ============
for resumo, nome in [(rc, "comparacoes"), (rm, "movimentos")]:
    for ent in ENTRADAS:
        fig, ax = plt.subplots(figsize=(8, 5))
        for alg in ALGORITMOS:
            d = dados(resumo, alg, ent)
            if d.empty:
                continue
            ax.plot(d["n"], d["mean"], "o-", label=alg)
        n = np.array(sorted(resumo["n"].unique()), dtype=float)
        ax.plot(n, n ** 2 / 2, "k--", lw=1, label="n²/2")
        ax.plot(n, n * np.log2(n), "k:", lw=1, label="n log₂ n")
        ax.plot(n, n, "k-.", lw=1, label="n")
        ax.set(xscale="log", yscale="log", xlabel="n", ylabel=f"nº de {nome}",
               title=f"{nome.capitalize()} - entrada {ent}")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8)
        fig.savefig(f"graficos/{nome}_{ent}.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

# ============ 7. Expoente empirico (inclinacao no log-log) ============
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

# ============ 8. Tabela compacta para os slides (ms) ============
tab = rt[(rt.entrada == "aleatorio") & (rt.n.isin([10000, 50000]))].copy()
tab["texto"] = ((tab["mean"] * 1000).map("{:.2f}".format) + " ± "
                + (tab["std"] * 1000).map("{:.2f}".format))
tab = tab.pivot(index="algoritmo", columns="n", values="texto")
tab.to_csv("resultados/tabela_slides_ms.csv")
print("\nTempo médio ± desvio padrão (ms), entrada aleatória:")
print(tab)

# ============ 9. Custo da mediana das medianas na entrada aleatoria ============
pv = rt[rt.entrada == "aleatorio"].pivot(index="n", columns="algoritmo", values="mean")
fator = (pv["quick_mm"] / pv["quick"]).round(2)
fator.to_csv("resultados/fator_quick_mm.csv", header=["quick_mm/quick"])
print("\nQuanto o quick_mm é mais lento que o quick (entrada aleatória):")
print(fator)

# ============ 10. Verificacoes exatas com a teoria ============
sel = rc[rc.algoritmo == "selection"]
ok = (sel["mean"] == sel["n"] * (sel["n"] - 1) / 2).all()
print(f"\nSelection faz exatamente n(n-1)/2 comparações em toda entrada: {ok}")
ins = rc[(rc.algoritmo == "insertion") & (rc.entrada == "ordenado")]
ok = (ins["mean"] == ins["n"] - 1).all()
print(f"Insertion (melhor caso) faz exatamente n-1 comparações: {ok}")
