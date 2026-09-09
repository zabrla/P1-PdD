"""
Visualizacao (matplotlib) do algoritmo em bst_core.py: gera 2 GIFs,
um pra cripto e um pra decripto, cada um com as 4 etapas do processo.

Uso direto (funcoes soltas):
    from .bst_visualizacao import animar_cripto, animar_decripto
    resultado = animar_cripto("minha-senha", "texto secreto", "cripto.gif")
    # resultado = {"cifra": "...", "gif": "cripto.gif"}

"""

import math

import matplotlib

matplotlib.use("Agg")  # backend sem tela -- TEM que vir antes do import do pyplot

import matplotlib.pyplot as plt
from django.conf import settings
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Circle

from .bst_core import PERCURSOS, BalancedBST, _ordem_embaralhada, cifrar, decifrar

# ======================================================================
# AUXILIARES DE DESENHO (usados pelas duas animacoes abaixo)
# ======================================================================


def _posicoes_layout(raiz):
    """Calcula (x, y) de cada no: x = posicao em-ordem (deixa a arvore
    legivel, sem cruzar galhos), y = -profundidade (raiz no topo)."""
    posicoes = {}
    contador = [0]

    def walk(no, profundidade):
        if no is None:
            return
        walk(no.left, profundidade + 1)
        posicoes[id(no)] = (contador[0], -profundidade)
        contador[0] += 1
        walk(no.right, profundidade + 1)

    walk(raiz, 0)
    return posicoes


def _profundidades(raiz):
    prof = {}

    def walk(no, d):
        if no is None:
            return
        prof[id(no)] = d
        walk(no.left, d + 1)
        walk(no.right, d + 1)

    walk(raiz, 0)
    return prof


def _nos_na_ordem(raiz, func_percurso):
    nos = []

    def walk_pre(n):
        if n:
            nos.append(n)
            walk_pre(n.left)
            walk_pre(n.right)

    def walk_in(n):
        if n:
            walk_in(n.left)
            nos.append(n)
            walk_in(n.right)

    def walk_post(n):
        if n:
            walk_post(n.left)
            walk_post(n.right)
            nos.append(n)

    caminhada = {
        BalancedBST.preorder: walk_pre,
        BalancedBST.inorder: walk_in,
        BalancedBST.postorder: walk_post,
    }[func_percurso]
    caminhada(raiz)
    return nos


def _rotulo_valor(valor):
    if valor is None:
        return "?"
    return chr(valor) if 32 <= valor < 127 else str(valor)


def _desenhar_arestas(ax, no, posicoes):
    if no is None:
        return
    x0, y0 = posicoes[id(no)]
    for filho in (no.left, no.right):
        if filho:
            x1, y1 = posicoes[id(filho)]
            ax.plot([x0, x1], [y0, y1], color="#9AA5B1", zorder=1, linewidth=2)
            _desenhar_arestas(ax, filho, posicoes)


def _desenhar_embaralhamento(ax, fig, dados, ordem, n, k, titulo):
    for pos in range(n):
        b = dados[pos]
        c = chr(b) if 32 <= b < 127 else "?"
        ax.add_patch(
            plt.Rectangle(
                (pos, 1.3), 0.9, 0.9, facecolor="#ECEFF1", edgecolor="#37474F"
            )
        )
        ax.text(
            pos + 0.45, 1.75, f"pos {pos}\n'{c}'", ha="center", va="center", fontsize=8
        )
    for r in range(n):
        ax.add_patch(
            plt.Rectangle((r, -0.6), 0.9, 0.9, facecolor="#ECEFF1", edgecolor="#37474F")
        )
    for r in range(min(k + 1, n)):
        pos_original = ordem[r]
        b = dados[pos_original]
        c = chr(b) if 32 <= b < 127 else "?"
        ax.annotate(
            "",
            xy=(r + 0.45, 0.3),
            xytext=(pos_original + 0.45, 1.3),
            arrowprops=dict(arrowstyle="->", color="#C0392B", lw=1.6),
        )
        ax.text(
            r + 0.45,
            -0.15,
            f"rank {r}\n'{c}'",
            ha="center",
            va="center",
            fontsize=8,
            color="#1C3D5A",
            fontweight="bold",
        )
    ax.set_xlim(-0.5, max(n, 1))
    ax.set_ylim(-1.1, 2.5)
    ax.axis("off")
    ax.text(-0.4, 1.95, "posição\noriginal", fontsize=8, color="#7F8C8D", ha="right")
    ax.text(-0.4, 0.0, "ordem\nembaralhada", fontsize=8, color="#7F8C8D", ha="right")
    fig.suptitle(f"{titulo}  ({k + 1}/{max(n, 1)})", fontsize=12, fontweight="bold")


def _desenhar_token(ax, fig, token, titulo):
    percurso_bin, resto = token.split("$", 1)
    cifra_hex, resto2 = resto.split("#", 1)
    n_bin, tamanho_real_bin = resto2.split("#", 1)
    partes = [
        ("percurso\n(binário)", percurso_bin, "#C0392B"),
        ("cifra\n(hex, real+lixo)", cifra_hex, "#2E5C8A"),
        ("tamanho total\n(binário)", n_bin, "#8E44AD"),
        ("tamanho real\n(binário)", tamanho_real_bin, "#27AE60"),
    ]
    x = 0
    for i, (rotulo, valor, cor) in enumerate(partes):
        largura_caixa = max(1.2, len(valor) * 0.5)
        ax.add_patch(
            plt.Rectangle(
                (x, 0), largura_caixa, 1, facecolor=cor, edgecolor="black", alpha=0.85
            )
        )
        ax.text(
            x + largura_caixa / 2,
            0.65,
            valor or "(vazio)",
            ha="center",
            va="center",
            fontsize=10,
            color="white",
            fontweight="bold",
        )
        y_rotulo = -0.35 if i % 2 == 0 else -0.65
        ax.text(
            x + largura_caixa / 2,
            y_rotulo,
            rotulo,
            ha="center",
            va="center",
            fontsize=8.5,
            color="#37474F",
        )
        x += largura_caixa + 0.3
    ax.set_xlim(-0.3, x)
    ax.set_ylim(-1.1, 1.4)
    ax.axis("off")
    fig.suptitle(titulo, fontsize=12, fontweight="bold")


# ======================================================================
# ANIMACAO DA CRIPTO (4 etapas -> 1 GIF)
# ======================================================================


def animar_cripto(chave: str, texto: str, caminho_gif: str):
    token, arvore, percurso = cifrar(chave, texto, _debug=True)
    nome_percurso, func = PERCURSOS[percurso]
    tamanho_real = len(texto.encode("utf-8"))

    nos_ordem = _nos_na_ordem(arvore.root, func)
    n = len(nos_ordem)
    dados = [None] * n
    for no in nos_ordem:
        pos, valor = no.value
        dados[pos] = valor

    ordem = _ordem_embaralhada(chave, n)
    prof = _profundidades(arvore.root)
    posicoes = _posicoes_layout(arvore.root)
    d_max = max(prof.values()) if prof else 0

    L_HEX, L_EMB, L_PERC, L_FIM = max(n, 1), max(n, 1), max(n, 1), 1
    cortes = [
        0,
        L_HEX,
        L_HEX + L_EMB,
        L_HEX + L_EMB + L_PERC,
        L_HEX + L_EMB + L_PERC + L_FIM,
    ]
    total_frames = cortes[-1]

    fig, ax = plt.subplots(figsize=(8, 8))

    def etapa_hex(i):
        for pos in range(n):
            b = dados[pos]
            eh_lixo = pos >= tamanho_real
            c = chr(b) if 32 <= b < 127 else "?"
            ax.add_patch(
                plt.Rectangle(
                    (pos, 1),
                    0.9,
                    0.9,
                    facecolor="#FBE9E7" if eh_lixo else "#ECEFF1",
                    edgecolor="#37474F",
                )
            )
            ax.text(
                pos + 0.45,
                1.45,
                c,
                ha="center",
                va="center",
                fontsize=13,
                fontweight="bold",
                color="#BF360C" if eh_lixo else "black",
            )
            if pos <= i:
                ax.add_patch(
                    plt.Rectangle(
                        (pos, -0.1),
                        0.9,
                        0.9,
                        facecolor="#E67E22" if eh_lixo else "#4C72B0",
                        edgecolor="#1C3D5A",
                    )
                )
                ax.text(
                    pos + 0.45,
                    0.35,
                    f"{b:02x}",
                    ha="center",
                    va="center",
                    fontsize=11,
                    color="white",
                )
        ax.set_xlim(-0.5, max(n, 1))
        ax.set_ylim(-0.3, 2.1)
        ax.set_aspect("auto")
        ax.axis("off")
        fig.suptitle(
            f"Passo 1/4 — Texto → bytes → hexadecimal (+ {n - tamanho_real} de lixo)  ({i + 1}/{max(n, 1)})",
            fontsize=12,
            fontweight="bold",
        )

    def etapa_final():
        _desenhar_token(
            ax, fig, token, "Passo 4/4 — Token final: percurso $ cifra # total # real"
        )

    def etapa_percurso(j):
        _desenhar_arestas(ax, arvore.root, posicoes)
        for idx, no in enumerate(nos_ordem):
            x, y = posicoes[id(no)]
            cor = "#66BB6A" if idx < j else ("#E53935" if idx == j else "#B0BEC5")
            ax.add_patch(
                Circle(
                    (x, y),
                    0.4,
                    facecolor=cor,
                    edgecolor="#37474F",
                    linewidth=1.5,
                    zorder=2,
                )
            )
            pos_original, _ = no.value
            ax.text(
                x,
                y,
                f"r={no.key}\npos={pos_original}",
                ha="center",
                va="center",
                fontsize=6.3,
                color="white",
                zorder=3,
            )
        ax.set_xlim(-1, n + 1)
        ax.set_ylim(-d_max - 2.6, 1.6)
        ax.set_aspect("auto")
        altura_real = arvore.height()
        altura_teorica = math.ceil(math.log2(n + 1)) if n > 0 else 0
        balanceada = (
            "balanceada ✓" if altura_real == altura_teorica else "DESBALANCEADA ✗"
        )
        ax.text(
            n / 2,
            1.35,
            f"altura = {altura_real}    ⌈log₂(n+1)⌉ = {altura_teorica}    {balanceada}",
            ha="center",
            va="center",
            fontsize=9,
            color="#1C2833",
            bbox=dict(
                boxstyle="round,pad=0.3", facecolor="#EAF2F8", edgecolor="#1C3D5A"
            ),
        )
        cifra_ate_agora = bytes(no.value[1] for no in nos_ordem[: j + 1])
        ax.text(
            n / 2,
            -d_max - 2.0,
            f"cifra até agora (hex): {cifra_ate_agora.hex()}",
            ha="center",
            va="center",
            fontsize=10,
            color="#1C2833",
            bbox=dict(
                boxstyle="round,pad=0.3", facecolor="#EAF2F8", edgecolor="#1C3D5A"
            ),
        )
        ax.axis("off")
        fig.suptitle(
            f"Passo 3/4 — Percorrendo em {nome_percurso}  ({j + 1}/{n})",
            fontsize=12,
            fontweight="bold",
        )

    def update(frame):
        ax.clear()
        if cortes[0] <= frame < cortes[1]:
            etapa_hex(frame - cortes[0])
        elif cortes[1] <= frame < cortes[2]:
            _desenhar_embaralhamento(
                ax,
                fig,
                dados,
                ordem,
                n,
                frame - cortes[1],
                "Passo 2/4 — Embaralhando posições com a chave",
            )
        elif cortes[2] <= frame < cortes[3]:
            etapa_percurso(frame - cortes[2])
        else:
            etapa_final()
        return []

    anim = FuncAnimation(
        fig, update, frames=total_frames, interval=350, repeat=False, blit=False
    )
    anim.save(caminho_gif, writer=PillowWriter(fps=3))
    plt.close(fig)
    return {"cifra": token, "gif": caminho_gif}


# ======================================================================
# ANIMACAO DA DECRIPTO (4 etapas -> 1 GIF, caminho inverso da cripto)
# ======================================================================


def animar_decripto(chave: str, token: str, caminho_gif: str):
    texto, arvore, percurso = decifrar(chave, token, _debug=True)
    nome_percurso, func = PERCURSOS[percurso]

    _, resto_tok = token.split("$", 1)
    _, resto_tok2 = resto_tok.split("#", 1)
    n_bin, tamanho_real_bin = resto_tok2.split("#", 1)
    n = int(n_bin, 2)
    tamanho_real = int(tamanho_real_bin, 2)

    ordem = _ordem_embaralhada(chave, n)
    nos_ordem = _nos_na_ordem(arvore.root, func)
    prof = _profundidades(arvore.root)
    posicoes = _posicoes_layout(arvore.root)
    d_max = max(prof.values()) if prof else 0
    dados_finais = [no.value[1] for no in sorted(nos_ordem, key=lambda no: no.value[0])]

    L_TOKEN, L_EMB, L_PERC, L_HEX = 1, max(n, 1), max(n, 1), max(n, 1)
    cortes = [
        0,
        L_TOKEN,
        L_TOKEN + L_EMB,
        L_TOKEN + L_EMB + L_PERC,
        L_TOKEN + L_EMB + L_PERC + L_HEX,
    ]
    total_frames = cortes[-1]

    fig, ax = plt.subplots(figsize=(8, 8))

    def etapa_hex_final(i):
        for pos in range(n):
            b = dados_finais[pos]
            eh_lixo = pos >= tamanho_real
            c = chr(b) if 32 <= b < 127 else "?"
            ax.add_patch(
                plt.Rectangle(
                    (pos, -0.1), 0.9, 0.9, facecolor="#ECEFF1", edgecolor="#37474F"
                )
            )
            if pos <= i:
                cor = "#E67E22" if eh_lixo else "#4C72B0"
                ax.add_patch(
                    plt.Rectangle(
                        (pos, 1), 0.9, 0.9, facecolor=cor, edgecolor="#1C3D5A"
                    )
                )
                ax.text(
                    pos + 0.45,
                    1.45,
                    f"{b:02x}",
                    ha="center",
                    va="center",
                    fontsize=11,
                    color="white",
                )
                rotulo = "✗" if eh_lixo else c
                ax.text(
                    pos + 0.45,
                    0.35,
                    rotulo,
                    ha="center",
                    va="center",
                    fontsize=13,
                    fontweight="bold",
                    color="#BF360C" if eh_lixo else "black",
                )
        ax.set_xlim(-0.5, max(n, 1))
        ax.set_ylim(-0.3, 2.1)
        ax.set_aspect("auto")
        ax.axis("off")
        fig.suptitle(
            f"Passo 4/4 — Hex → bytes → texto (descartando {n - tamanho_real} de lixo)  ({i + 1}/{max(n, 1)})",
            fontsize=12,
            fontweight="bold",
        )

    def etapa_percurso(j):
        _desenhar_arestas(ax, arvore.root, posicoes)
        for idx, no in enumerate(nos_ordem):
            x, y = posicoes[id(no)]
            cor = "#66BB6A" if idx < j else ("#E53935" if idx == j else "#B0BEC5")
            ax.add_patch(
                Circle(
                    (x, y),
                    0.4,
                    facecolor=cor,
                    edgecolor="#37474F",
                    linewidth=1.5,
                    zorder=2,
                )
            )
            pos_original, valor = no.value
            ax.text(
                x,
                y,
                f"r={no.key}\npos={pos_original}",
                ha="center",
                va="center",
                fontsize=6.3,
                color="white",
                zorder=3,
            )
        ax.set_xlim(-1, n + 1)
        ax.set_ylim(-d_max - 3.3, 1.6)
        ax.set_aspect("auto")
        altura_real = arvore.height()
        altura_teorica = math.ceil(math.log2(n + 1)) if n > 0 else 0
        balanceada = (
            "balanceada ✓" if altura_real == altura_teorica else "DESBALANCEADA ✗"
        )
        ax.text(
            n / 2,
            1.35,
            f"altura = {altura_real}    ⌈log₂(n+1)⌉ = {altura_teorica}    {balanceada}",
            ha="center",
            va="center",
            fontsize=9,
            color="#1C2833",
            bbox=dict(
                boxstyle="round,pad=0.3", facecolor="#EAF2F8", edgecolor="#1C3D5A"
            ),
        )
        caixa_w = 0.9
        for pos in range(n):
            ax.add_patch(
                plt.Rectangle(
                    (pos, -d_max - 2.9),
                    caixa_w,
                    0.8,
                    facecolor="white",
                    edgecolor="#37474F",
                    linewidth=1,
                    zorder=2,
                )
            )
        for idx in range(j + 1):
            no = nos_ordem[idx]
            pos_original, valor = no.value
            ax.text(
                pos_original + caixa_w / 2,
                -d_max - 2.5,
                _rotulo_valor(valor),
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                zorder=3,
            )
        ax.axis("off")
        fig.suptitle(
            f"Passo 3/4 — Percorrendo em {nome_percurso}, devolvendo à posição  ({j + 1}/{n})",
            fontsize=12,
            fontweight="bold",
        )

    def update(frame):
        ax.clear()
        if cortes[0] <= frame < cortes[1]:
            _desenhar_token(
                ax,
                fig,
                token,
                "Passo 1/4 — Token recebido: percurso $ cifra # total # real",
            )
        elif cortes[1] <= frame < cortes[2]:
            _desenhar_embaralhamento(
                ax,
                fig,
                dados_finais,
                ordem,
                n,
                frame - cortes[1],
                "Passo 2/4 — Reconstruindo a ordem embaralhada (mesma chave)",
            )
        elif cortes[2] <= frame < cortes[3]:
            etapa_percurso(frame - cortes[2])
        else:
            etapa_hex_final(frame - cortes[3])
        return []

    anim = FuncAnimation(
        fig, update, frames=total_frames, interval=350, repeat=False, blit=False
    )
    anim.save(caminho_gif, writer=PillowWriter(fps=3))
    plt.close(fig)
    return {"texto": texto, "gif": caminho_gif}


# ======================================================================
# CLASSE (embrulha cifrar/decifrar/animar como metodos, guardando a chave)
# ======================================================================


class BSTCripto:
    """
    Wrapper orientado a objeto em cima das funcoes de bst_core e das
    animacoes deste arquivo. Guarda a chave uma vez no construtor.

    Exemplo (dentro de uma view/service do Django):
        from django.conf import settings
        from .bst_visualizacao import BSTCripto

        bst = BSTCripto(settings.BST_CHAVE)
        resultado = bst.animar_cripto("texto secreto", "cripto.gif")
        # {"cifra": "...", "gif": "cripto.gif"}
    """

    def __init__(self):
        self.chave = settings.BST_CHAVE

    def cifrar(self, texto: str, lixo_max: int = 64) -> str:
        return cifrar(self.chave, texto, lixo_max=lixo_max)

    def decifrar(self, token: str) -> str:
        return decifrar(self.chave, token)

    def animar_cripto(self, texto: str, caminho_gif: str) -> dict:
        return animar_cripto(self.chave, texto, caminho_gif)

    def animar_decripto(self, token: str, caminho_gif: str) -> dict:
        return animar_decripto(self.chave, token, caminho_gif)
