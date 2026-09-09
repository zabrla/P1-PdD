# Documentação de Arquitetura: Diagrama de Atividades — Comunicação P2P

Este documento descreve a modelagem do **Diagrama de Atividades** do sistema de comunicação *Peer-to-Peer* (P2P), detalhando o fluxo operacional, regras de transição, atores envolvidos e manipulação de dados em memória e armazenamento local.

---

## 1. Visão Geral

O sistema permite a troca de mensagens de forma segura e descentralizada, com suporte a ambientes **Web** e **Offline**. A arquitetura integra criptografia, armazenamento em estruturas de dados em memória — especificamente **Árvores Binárias de Busca (BST)** —, serialização em hexadecimal e persistência de dados exportáveis.

### 1.1 Objetivos da Documentação
* Mapear o ciclo de vida completo da sessão do usuário.
* Especificar os fluxos paralelos de processamento de mensagens e arquivos.
* Formalizar a rastreabilidade e auditoria via geração de logs.

---

## 2. Atores e Responsabilidades

| Ator | Tipo | Responsabilidades |
| :--- | :--- | :--- |
| **Usuário** | Humano / Cliente | Autenticação, entrada de mensagens, solicitação de operações de criptografia e gerenciamento de arquivos (import/export). |
| **Sistema** | Aplicação / Nó P2P | Validação de credenciais, gestão da sessão, construção/percurso da BST, criptografia/descriptografia, codificação Hex, persistência e auditoria. |

---

## 3. Especificação dos Fluxos de Atividade

### 3.1 Autenticação e Inicialização de Sessão
1. O usuário acessa a aplicação (Online ou Offline) e fornece as credenciais.
2. O **Sistema** valida as informações de acesso:
   * **Credenciais Inválidas:** Exibe mensagem de erro e encerra o fluxo (`[Fim]`).
   * **Credenciais Válidas:** Gera o log de auditoria de acesso e inicializa a camada de comunicação P2P.

---

### 3.2 Processos Principais (Paralelos)

Com a conexão P2P estabelecida, a aplicação disponibiliza três fluxos independentes e concorrentes:

* **1. Envio de Mensagem**
* **2. Exportação de Conversa**
* **3. Importação de Conversa**

#### Fluxo 1: Envio e Processamento de Mensagem
1. **Usuário:** Insere a mensagem de texto no cliente.
2. **Sistema:** Instancia, popula e exibe visualmente a Árvore Binária de Busca (**BST**) na interface.
3. **Usuário:** Solicita a criptografia do conteúdo.
4. **Sistema:** Executa o percurso na BST, converte a estrutura/conteúdo para **Hexadecimal** e registra o log da operação.

#### Fluxo 2: Exportação de Conversa
1. **Usuário:** Solicita o salvamento local do histórico.
2. **Sistema:** Compila os dados criptografados e gera o arquivo físico local.
3. **Usuário:** Realiza o download do arquivo.
4. **Sistema:** Registra o log da auditoria de download/exportação.

#### Fluxo 3: Importação e Reconstrução de Conversa
1. **Usuário:** Submete um arquivo criptografado local.
2. **Sistema:** Efetua a leitura do conteúdo codificado em **Hexadecimal** e reconstrói a **BST** em memória.
3. **Sistema:** Executa a descriptografia das mensagens e exibe os dados e a árvore na interface.
4. **Sistema:** Registra o log da operação de importação.

---

### 3.3 Auditoria e Rastreabilidade (Logs)

O sistema dispara eventos de log assíncronos nos seguintes marcos operacionais:
* Autenticação e abertura de sessão;
* Criptografia e envio de payload;
* Exportação e download de dados;
* Importação e parsing de arquivos.

---

### 3.4 Encerramento da Sessão

1. O **Usuário** encerra o cliente ou fecha a aba do navegador.
2. O **Sistema** intercepta o evento, invalida/expira os tokens de sessão ativos em memória e encerra o processo.

---

## 4. Diagrama de atividades

![diagrama de atividades](<../imgs/Diagrama de Atividade (doc).jpg>)