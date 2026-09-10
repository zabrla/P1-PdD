# Criptografia com BST balanceada + percurso

Esquema de criptografia/decriptografia simétrica usando **árvore binária
de busca balanceada** e **percurso** (pré-ordem, em-ordem ou pós-ordem)
como mecanismo central. Hexadecimal e binário são só formato de
serialização da saída — não fazem parte do núcleo do algoritmo.

> **Aviso de escopo:** exercício acadêmico de estrutura de dados
> aplicada. Não é uma cifra criptograficamente forte — ver seção
> "Limitações de segurança" no final antes de usar em qualquer coisa
> que precise de confidencialidade real.

**Arquivos:**
- `bst_core.py` — algoritmo puro (`cifrar`/`decifrar`), sem matplotlib. Pode ser importado sozinho, sem instalar nada além da stdlib.
- `bst_visualizacao.py` — as animações (`animar_cripto`/`animar_decripto`) e a classe `BSTCripto`, que importa de `bst_core.py`.

**Uso funcional:**
```python
from bst_core import cifrar, decifrar
token = cifrar("minha-senha", "texto secreto")
texto = decifrar("minha-senha", token)
```

**Uso via classe (guarda a chave, gera GIF):**
```python
from bst_visualizacao import BSTCripto

bst = BSTCripto("minha-senha")

# cripto: busca a cifra E o gif no mesmo dicionário
resultado_cripto = bst.animar_cripto("texto secreto", "cripto.gif")
cifra = resultado_cripto["cifra"]   # o token cifrado (string)
gif_cripto = resultado_cripto["gif"]  # "cripto.gif"

# decripto: busca o texto E o gif no mesmo dicionário
resultado_decripto = bst.animar_decripto(cifra, "decripto.gif")
texto = resultado_decripto["texto"]     # "texto secreto"
gif_decripto = resultado_decripto["gif"]  # "decripto.gif"
```

---

## 1. Visão geral do algoritmo

```
CIFRAR
  texto (string)
     │  .encode("utf-8")
     ▼
  bytes reais (posição 0..tamanho_real-1)
     │  + lixo aleatório (0 a 64 bytes, via secrets — não vem da chave)
     ▼
  bytes totais (real + lixo), na posição 0..n-1
     │  chave embaralha as posições (Fisher-Yates)
     ▼
  cada posição recebe um "rank" (onde caiu no embaralho)
     │  monta-se uma BST balanceada, indexada pelo rank
     ▼
  árvore balanceada (montada por bisseção, sem rotação)
     │  percorre (percurso sorteado: pré/em/pós-ordem)
     ▼
  bytes na ordem visitada = CIFRA
     │  serializa em hex + binário
     ▼
  token final: "<percurso_bin>$<cifra_hex>#<tamanho_total_bin>#<tamanho_real_bin>"


DECIFRAR (caminho inverso)
  token
     │  separa percurso, cifra, tamanho total e tamanho real
     ▼
  reconstrói a MESMA árvore (mesma chave + tamanho total = mesmo rank = mesma forma)
     │  percorre com o MESMO percurso gravado no token
     ▼
  associa cada byte recebido à posição original do nó visitado
     │  reordena pro array indexado por posição (real + lixo)
     ▼
  descarta tudo após o tamanho_real (o lixo)
     │  .decode("utf-8")
     ▼
  texto original
```

A **única fonte de segredo** é a senha: ela determina como as posições
são embaralhadas antes de montar a árvore. A árvore em si é sempre
balanceada e construída da mesma forma (por bisseção); o que muda com
a chave é a ORDEM em que as posições entram nessa bisseção. O lixo
aleatório no final NÃO depende da chave — vem de `secrets`, uma fonte
de aleatoriedade de verdade, gerada a cada chamada.

---

## 2. Por que existe lixo (padding aleatório)

Sem o lixo, `_ordem_embaralhada(chave, n)` depende só da chave e do
tamanho da mensagem. Isso significa que **toda mensagem do mesmo
tamanho, sob a mesma chave, gera a mesma forma de árvore** — em um
chat com muitas mensagens trocadas sob a mesma chave, isso é o cenário
clássico de "reuso de chave de transposição": quanto mais mensagens um
atacante acumula, mais fácil fica atacar (ele pode comparar a mesma
posição entre várias mensagens).

Colando de 0 a 64 bytes de lixo aleatório depois do texto real antes de
cifrar:
- o tamanho total passa a variar a cada chamada, mesmo pra mensagens
  idênticas — isso já evita o reuso de forma de árvore entre mensagens;
- atrapalha análise de frequência/bigrama, que fica com menos sinal
  real (a mensagem) proporcional ao ruído (o lixo).

O tamanho real fica gravado separado no token (`tamanho_real`), pra
decifrar saber exatamente quantos bytes descartar no final.

**Isso NÃO faz a cifra ficar forte** — só reduz esse problema
específico. Ver seção 7.

---

## 3. Estruturas e funções

### `class _Node`
Nó da árvore: `key` (o rank), `value` (tupla `(posição_original, byte)`),
`left`, `right`.

### `class BalancedBST`
| Método | O que faz |
|---|---|
| `build_sorted(pairs)` | Monta a árvore de uma vez a partir de uma lista `(key, value)` **já ordenada por key**. |
| `_build(pairs)` | Recursão: pega o elemento do meio como raiz, resto vai pra esquerda/direita. |
| `preorder()` / `inorder()` / `postorder()` | Os 3 percursos clássicos. |
| `height()` | Altura da árvore (usada na visualização, prova o balanceamento). |

Por ser montada de uma vez por bisseção (nunca por inserção nó a nó),
a altura é **sempre** `⌈log2(n+1)⌉` — não depende de sorte nem precisa
de rotação (AVL, red-black, etc.).

### `_ordem_embaralhada(chave, n)`
Usa `random.Random(chave)` (a senha como semente) para embaralhar as
posições `0..n-1`. É o único ponto onde a chave entra no algoritmo.

### `_montar_arvore(chave, n, dados)`
Converte a ordem embaralhada em `rank` (o inverso da ordem), monta os
pares `(rank, (posição, byte))` ordenados por rank, e constrói a árvore.
Com `dados=None` (usado na decriptografia), o byte fica `None` até ser
preenchido depois do percurso.

### `cifrar(chave, texto, _debug=False, lixo_max=64) -> str`
Sorteia um percurso, gera lixo aleatório, monta a árvore, percorre,
serializa. `_debug=True` também devolve `(arvore, percurso)`.

### `decifrar(chave, token, _debug=False) -> str`
Faz o caminho inverso e descarta o lixo. `_debug=True` também devolve
a árvore reconstruída (já com os valores recuperados).

### `animar_cripto(chave, texto, caminho_gif) -> dict`
Gera o GIF e devolve `{"cifra": <token cifrado>, "gif": <caminho_gif>}`.

### `animar_decripto(chave, token, caminho_gif) -> dict`
Gera o GIF e devolve `{"texto": <texto decifrado>, "gif": <caminho_gif>}`.

### `class BSTCripto(chave)`
Wrapper orientado a objeto (em `bst_visualizacao.py`) — guarda a chave
no construtor e expõe os 4 métodos acima sem precisar repetir a chave
em toda chamada: `.cifrar(texto)`, `.decifrar(token)`,
`.animar_cripto(texto, caminho_gif)`, `.animar_decripto(token, caminho_gif)`.

---

## 4. Formato do token

```
<percurso_bin>$<cifra_hex>#<tamanho_total_bin>#<tamanho_real_bin>
```

| Campo | Significado | Exemplo |
|---|---|---|
| `percurso_bin` | `0`=pré-ordem, `1`=em-ordem, `10`=pós-ordem (binário) | `1` |
| `cifra_hex` | bytes cifrados (texto real + lixo), em hex | `c68d82...` |
| `tamanho_total_bin` | quantos bytes entraram na árvore (real + lixo), binário | `110010` (=50) |
| `tamanho_real_bin` | quantos desses bytes são texto de verdade, binário | `1001` (=9) |

Exemplo: `cifrar("senha-do-anderson", "ALGORITMO")` gera algo como
`1$c68d82b2eb...#110010#1001` — tamanho total e cifra mudam a cada
chamada (por causa do lixo aleatório), mas sempre decifra de volta
para `"ALGORITMO"` com a mesma chave.

---

## 5. As 4 etapas (visualização)

**`animar_cripto`** (gera `cripto.gif`):
1. Texto → bytes → hexadecimal (lixo já aparece, em cor diferente)
2. Embaralhando posições com a chave (setas posição → rank)
3. Percorrendo no percurso sorteado — cifra se formando, com a
   altura real vs. `⌈log₂(n+1)⌉` mostrada junto (prova o balanceamento)
4. Token final: as 4 partes coloridas

**`animar_decripto`** (gera `decripto.gif`):
1. Token recebido — as 4 partes
2. Reconstruindo a ordem embaralhada (mesma chave)
3. Percorrendo e devolvendo cada byte à posição original (fita
   preenche fora de ordem), com a mesma prova de balanceamento
4. Hex → bytes → texto, descartando o lixo (marcado com ✗)

GIFs quadrados (800×800) e 330ms por quadro.

---

## 6. Complexidade (Big-O)

| Etapa | Custo |
|---|---|
| Gerar lixo aleatório | O(lixo_max) = O(1) |
| Embaralhar posições (Fisher-Yates) | O(n) |
| Ordenar pares por rank | O(n log n) |
| Montar árvore por bisseção | O(n log n) |
| Percurso (visita cada nó 1x) | O(n) |
| Serialização hex/binário | O(n) |

**Total: O(n log n) tanto para cifrar quanto para decifrar** (n =
tamanho real + lixo, no máximo tamanho_real + 64). Espaço: O(n).
Rápido o bastante pra tempo real em mensagens de chat (microssegundos
a milissegundos para textos de até milhares de caracteres).

---

## 7. Limitações de segurança (leia antes de usar em produção)

Este esquema **não é criptograficamente forte**. Testado nesta mesma
conversa:

1. **É transposição pura, sem substituição** — só reordena bytes,
   nunca troca um valor por outro. O conjunto de caracteres do texto
   (mais o lixo) fica exposto, só a ordem muda. Um ataque de busca
   heurística por estatística de letras (técnica clássica contra
   cifra de transposição) já recupera fragmentos legíveis sem
   conhecer a chave — e uma IA tende a ir além disso. O lixo aleatório
   reduz esse risco (mais ruído, menos sinal), mas não elimina.

2. **`random.Random(chave)` não é criptográfico** — determinístico,
   não resiste a força bruta/dicionário sobre a senha.

3. **Troca de chave não é resolvida por este script.** A cifra
   pressupõe que os dois lados já compartilham a chave por um canal
   seguro (combinada fora do chat, por exemplo). Derivar a chave de
   IDs de usuário não funciona — o backend do chat normalmente
   enxerga os dois IDs, o que anula a proteção contra ele.

**Separação de responsabilidades recomendada para uso em chat:**
- **Confidencialidade do conteúdo:** este algoritmo (contra vazamento
  de banco de dados/backup, não contra o próprio backend).
- **Controle de acesso** (só dono e destinatário conseguem sequer
  consultar a mensagem): modelagem do banco + autorização no backend
  — responsabilidade separada, não é papel da cifra.

Para proteção real de dado sensível, use bibliotecas testadas
(`cryptography`/Fernet, AES-GCM, libsodium) em vez deste esquema.
