"""
Nucleo do algoritmo de criptografia: BST balanceada + um dos 3 percursos.
Sem dependencias de visualizacao (sem matplotlib) -- so o que e
necessario pra cifrar/decifrar de verdade.

Hexadecimal e binario sao so o formato de saida (o "plus"), nao fazem
parte do nucleo do algoritmo. Cada cifra tambem recebe uma quantidade
aleatoria de bytes de lixo (0-64) coladas apos o texto real, pra evitar
que a mesma chave sempre gere a mesma forma de arvore.

Uso basico:
    from bst_core import cifrar, decifrar
    token = cifrar("minha-senha", "texto secreto")
    texto = decifrar("minha-senha", token)
"""

import random
import secrets

# ======================================================================
# ESTRUTURA DA ARVORE
# ======================================================================


class _Node:
    __slots__ = (
        "key",
        "left",
        "right",
        "value",
    )  # sem __dict__ por no, so economia de memoria

    def __init__(self, key, value):
        self.key = key  # chave de busca (aqui: o "rank" da posicao, ver _montar_arvore)
        self.value = value  # o que o no carrega: (posicao_original, byte)
        self.left = None  # filho esquerdo (chaves menores que 'key')
        self.right = None  # filho direito (chaves maiores que 'key')


class BalancedBST:
    """Montada de uma vez por bisseccao de uma lista ja ordenada por key.
    Sempre perfeitamente balanceada (altura = log2(n+1)), sem rotacao."""

    def __init__(self):
        self.root = None  # arvore vazia ate build_sorted ser chamado

    def build_sorted(self, pairs):
        # pairs PRECISA chegar aqui ja ordenado por chave crescente --
        # essa e a pre-condicao que garante uma BST valida na saida.
        self.root = self._build(pairs)

    def _build(self, pairs):
        if not pairs:  # fatia vazia -> nao ha no aqui
            return None
        mid = len(pairs) // 2  # indice do elemento do meio da fatia
        key, value = pairs[mid]  # esse elemento do meio vira a raiz desta sub-arvore
        node = _Node(key, value)  # cria o no raiz
        node.left = self._build(
            pairs[:mid]
        )  # tudo antes do meio -> sub-arvore esquerda
        node.right = self._build(
            pairs[mid + 1 :]
        )  # tudo depois do meio -> sub-arvore direita
        return node  # devolve a raiz desta sub-arvore pro chamador

    def preorder(self):
        out = []  # lista que vai acumular (chave, valor) visitados

        def walk(n):  # busca em profundidade recursiva
            if n:  # se o no existe (nao e None)
                out.append((n.key, n.value))  # 1) visita a RAIZ primeiro
                walk(n.left)  # 2) depois o filho esquerdo
                walk(n.right)  # 3) depois o filho direito

        walk(self.root)  # comeca a busca pela raiz da arvore toda
        return out  # devolve a lista na ordem pre-ordem

    def inorder(self):
        out = []

        def walk(n):
            if n:
                walk(n.left)  # 1) esquerda primeiro
                out.append((n.key, n.value))  # 2) raiz no meio
                walk(n.right)  # 3) direita por ultimo

        walk(self.root)
        return out  # sempre sai em ordem CRESCENTE de key

    def postorder(self):
        out = []

        def walk(n):
            if n:
                walk(n.left)  # 1) esquerda
                walk(n.right)  # 2) direita
                out.append((n.key, n.value))  # 3) raiz por ultimo

        walk(self.root)
        return out

    def height(self):
        # usado na visualizacao, pra provar que a altura fica em
        # log2(n+1) mesmo com n grande -- nao entra em cifrar/decifrar.
        def h(n):
            return 0 if n is None else 1 + max(h(n.left), h(n.right))

        return h(self.root)


# Tabela: codigo gravado na cifra -> (nome legivel, metodo da classe a chamar).
# "0"=pre-ordem, "1"=em-ordem, "2"=pos-ordem.
PERCURSOS = {
    "0": ("pre-ordem", BalancedBST.preorder),
    "1": ("em-ordem", BalancedBST.inorder),
    "2": ("pos-ordem", BalancedBST.postorder),
}


# ======================================================================
# NUCLEO DO ALGORITMO
# ======================================================================


def _ordem_embaralhada(chave: str, n: int):
    """
    Unico lugar onde a SENHA entra no algoritmo.

    Exemplo real: chave="senha-do-anderson", n=3 (texto "ABC")
        -> ordem = [1, 2, 0]
    Leitura: quem fica em 1o lugar do embaralho e a posicao 1 ('B'),
    em 2o lugar a posicao 2 ('C'), em 3o lugar a posicao 0 ('A').
    """
    rng = random.Random(chave)  # a chave vira a semente do gerador
    ordem = list(range(n))  # [0, 1, 2, ..., n-1] -- posicoes originais, em ordem
    rng.shuffle(
        ordem
    )  # embaralha essa lista IN-PLACE, de forma deterministica pra essa chave
    return ordem  # ordem[i] = "qual posicao original ficou no i-esimo lugar"


def _montar_arvore(chave: str, n: int, dados):
    """
    dados=None e usado no decifrar (ainda nao se sabe qual byte
    pertence a qual posicao -- so a FORMA da arvore importa ali).
    """
    ordem = _ordem_embaralhada(chave, n)  # ex.: [1, 2, 0]

    rank = [0] * n  # vai virar o inverso de 'ordem'
    for r, pos in enumerate(
        ordem
    ):  # r = lugar no embaralho (0,1,2,...), pos = posicao original
        rank[pos] = r  # rank[posicao_original] = em que lugar ela caiu
    # ex.: ordem=[1,2,0] -> rank=[2,0,1] (posicao 0 caiu no lugar 2, posicao 1 no lugar 0, posicao 2 no lugar 1)

    pares = sorted(
        ((rank[i], (i, dados[i] if dados else None)) for i in range(n)),
        # cada par: (chave_de_busca=rank[i], valor=(posicao_original=i, byte))
        key=lambda p: p[
            0
        ],  # ordena pelos rank crescente -- pre-condicao do build_sorted
    )
    arvore = BalancedBST()  # cria arvore vazia
    arvore.build_sorted(pares)  # monta por bisseccao, ja balanceada
    return arvore  # devolve pronta pra cifrar/decifrar percorrer


def cifrar(chave: str, texto: str, _debug: bool = False, lixo_max: int = 64):
    """
    O percurso e sorteado aleatoriamente a cada chamada (nao depende da
    chave). Alem disso, uma quantidade ALEATORIA de bytes de lixo
    (0 a lixo_max, sorteada com 'secrets' -- nao vem da chave, entao
    nao da pra prever nem reproduzir) e colada depois do texto real
    antes de cifrar. Isso resolve dois problemas:
      - sem lixo variavel, a MESMA chave + MESMO tamanho de mensagem
        sempre gera a MESMA forma de arvore/permutacao -- num chat
        com muitas mensagens sob a mesma chave, isso e exatamente o
        cenario de "reuso de chave de transposicao", que fica mais
        facil de atacar quanto mais mensagens o atacante acumula.
        Com lixo variavel, cada mensagem usa um tamanho (e portanto
        uma forma de arvore) diferente, mesmo repetindo o texto.
      - atrapalha analise de frequencia/bigrama, que fica com menos
        sinal real (a mensagem) proporcional ao ruido (o lixo).
    O tamanho REAL fica gravado separado no token, pra decifrar saber
    exatamente quantos bytes sao texto e quantos sao lixo a descartar.

    Exemplos reais (chave="senha-do-anderson", lixo varia a cada chamada):
        cifrar(chave, "ABC") -> algo como "0$434241f2a91c#1001#11"
        (percurso, cifra em hex -- aqui com 3 bytes de lixo cifrados
        junto --, tamanho TOTAL em binario, tamanho REAL em binario)
    Formato de saida: "<percurso_bin>$<cifra_hex>#<tamanho_total_bin>#<tamanho_real_bin>"

    _debug=True: alem do token, tambem devolve (arvore, percurso) usados
    internamente -- so pra quem quer inspecionar/desenhar a arvore (ver
    animar_cripto mais abaixo). Uso normal ignora isso.
    """
    percurso = random.choice(
        list(PERCURSOS)
    )  # sorteia "0", "1" ou "2" -- so pra escolher o percurso, sem ligacao com a chave
    dados_reais = list(
        texto.encode("utf-8")
    )  # string -> lista de bytes (UTF-8 cobre acentos/emoji)
    tamanho_real = len(dados_reais)  # quantos bytes o texto de verdade tem

    tamanho_lixo = secrets.randbelow(lixo_max + 1)  # 0..lixo_max, imprevisivel
    lixo = [
        secrets.randbelow(256) for _ in range(tamanho_lixo)
    ]  # bytes aleatorios de verdade (nao vem da chave)
    dados = dados_reais + lixo  # texto real + lixo colado no final
    n = len(dados)  # tamanho TOTAL (o que entra na arvore)

    arvore = _montar_arvore(
        chave, n, dados
    )  # monta a arvore ja com os bytes (reais + lixo) dentro

    _, func = PERCURSOS[
        percurso
    ]  # pega a funcao de percurso escolhida (preorder/inorder/postorder)
    visitados = func(
        arvore
    )  # lista [(rank, (posicao, byte)), ...] na ordem do percurso
    cifra = bytes(valor for _, (pos, valor) in visitados)
    # ^ descarta rank e posicao, fica so a sequencia de bytes na ordem visitada -- isso E a cifra

    token = (
        f"{bin(int(percurso))[2:]}${cifra.hex()}#{bin(n)[2:]}#{bin(tamanho_real)[2:]}"
    )
    # percurso: sorteado ("0"/"1"/"2"), escrito em binario, antes do "$"
    # cifra.hex(): bytes cifrados (reais + lixo) em hexadecimal, entre "$" e o 1o "#"
    # bin(n)[2:]: tamanho TOTAL (com lixo) em binario, entre os dois "#"
    # bin(tamanho_real)[2:]: tamanho REAL (sem lixo) em binario, depois do 2o "#"

    if _debug:
        return token, arvore, percurso
    return token


def decifrar(chave: str, token: str, _debug: bool = False):
    """
    Exemplos reais (chave="senha-do-anderson"):
        decifrar(chave, cifrar(chave, "ABC")) -> "ABC"  (sempre, independente do lixo sorteado)
    Com a chave ERRADA, o rank fica diferente, a arvore reconstruida
    fica diferente, e o resultado sai como lixo (ou da erro de UTF-8).

    _debug=True: tambem devolve a arvore reconstruida internamente,
    ja preenchida com os bytes recebidos -- incluindo o lixo, que so e
    descartado no final (pra visualizar/comparar com a arvore da cripto).
    """
    percurso_bin, resto = token.split("$", 1)  # tudo antes do "$" = percurso em binario
    cifra_hex, resto2 = resto.split("#", 1)  # antes do 1o "#" = cifra em hex
    n_bin, tamanho_real_bin = resto2.split(
        "#", 1
    )  # entre os "#" = tamanho total; depois = tamanho real
    percurso = str(int(percurso_bin, 2))  # binario -> int -> volta pra "0"/"1"/"2"
    n = int(n_bin, 2)  # binario -> tamanho TOTAL (com lixo)
    tamanho_real = int(tamanho_real_bin, 2)  # binario -> tamanho REAL (sem lixo)
    cifra = bytes.fromhex(cifra_hex)  # hex -> bytes de novo

    arvore = _montar_arvore(
        chave, n, None
    )  # reconstroi a MESMA arvore (mesma chave+n = mesmo rank = mesma forma)
    _, func = PERCURSOS[percurso]  # usa o mesmo percurso que foi gravado na cifra
    visitados = func(arvore)  # visita os nos na MESMA ordem de quando cifrou

    dados = [None] * n  # array final (real + lixo), indexado pela posicao ORIGINAL
    for (_, (pos, _)), c in zip(visitados, cifra):
        # o k-esimo no visitado "sabe" sua posicao original (pos);
        # o k-esimo byte da cifra pertence a esse no -- reassocia os dois
        dados[pos] = c

    # preenche o VALOR de cada no da arvore reconstruida, pra visualizacao
    # (nao e necessario pro algoritmo em si, so serve pro modo debug)
    if _debug:

        def preencher(n_):
            if n_ is None:
                return
            pos, _antigo = n_.value
            n_.value = (pos, dados[pos])
            preencher(n_.left)
            preencher(n_.right)

        preencher(arvore.root)

    texto = bytes(dados[:tamanho_real]).decode(
        "utf-8"
    )  # so os bytes REAIS (0..tamanho_real) -- o lixo e descartado aqui

    if _debug:
        return texto, arvore, percurso
    return texto
