# Documentação de Arquitetura: Fluxo de Navegação e Interação (Wireframes LQ)

Este documento descreve a modelagem Wireframes LowQuality, detalhando o fluxo operacional, transições de tela, atores envolvidos e as regras de manipulação, criptografia e descriptografia de arquivos.
ue
---

## 1. Visão Geral

O sistema web fornece uma interface intuitiva para troca de mensagens e gerenciamento seguro do histórico por meio de criptografia estruturada em árvores binárias. A documentação mapeia as interações do usuário desde o acesso inicial até a manipulação de arquivos (importação/exportação) e auditoria de ações.

### 1.1 Objetivos da Documentação

* Mapear o ciclo de vida completo da sessão do usuário e o fluxo de telas (Login -> Home -> Árvore/Logs).
* Especificar as regras de transição da interface na criptografia e descriptografia visual.
* Formalizar a rastreabilidade via tela de histórico de logs.

---

## 2. Atores e Responsabilidades

| Ator | Tipo | Responsabilidades |
| --- | --- | --- |
| **Usuário** | Humano / Cliente | Autenticação, interação com o chat, navegação no menu, solicitação de criptografia, seleção de arquivos locais para importação e solicitação de descriptografia. |
| **Sistema** | Aplicação Web | Gerenciamento de sessão, exibição e animação da Árvore Binária, processamento de arquivos (download automático e leitura local), e registro/exibição do histórico de Logs. |

---

## 3. Especificação dos Fluxos de Atividade

### 3.1 Autenticação e Inicialização de Sessão

1. O **Usuário** acessa a primeira tela da aplicação (Login).
2. O **Usuário** insere suas credenciais de acesso.
3. O **Sistema** processa o login e redireciona o usuário para a **Home**.

---

### 3.2 Processos Principais

A partir da **Home**, o usuário tem acesso imediato à interface do Chat e a três opções principais de navegação: **Árvore Binária**, **Logs** e **Sair**.

#### Fluxo 1: Visualização da Árvore e Criptografia (Exportação)

1. **Usuário:** Na tela Home, clica no botão "Árvore Binária".
2. **Sistema:** Apresenta na tela a estrutura de árvore binária correspondente à conversa atual, exibindo os botões "Criptografar" e "Importar".
3. **Usuário:** Clica no botão "Criptografar".
4. **Sistema:** Ilustra visualmente o processo de criptografia percorrendo a árvore binária.
5. **Sistema:** Finaliza o processo e realiza o download automático do arquivo criptografado no navegador para o disco local do dispositivo.

#### Fluxo 2: Importação e Descriptografia de Conversa

1. **Usuário:** Na tela de Árvore Binária, clica no botão "Importar".
2. **Sistema:** Abre o explorador de tarefas/gerenciador de arquivos nativo do sistema operacional.
3. **Usuário:** Seleciona um arquivo criptografado salvo em seu disco local.
4. **Sistema:** Carrega o arquivo na página, atualiza a interface e substitui o botão de criptografia pelo botão "Descriptografar".
5. **Usuário:** Clica no botão "Descriptografar".
6. **Sistema:** Ilustra visualmente o processo de descriptografia percorrendo a árvore binária.
7. **Sistema:** Redireciona/Carrega a nova conversa descriptografada em uma janela sobreposta, no mesmo modelo de chat da tela Home.

#### Fluxo 3: Acesso ao Histórico (Logs)

1. **Usuário:** Na tela Home, clica no botão "Logs".
2. **Sistema:** Exibe a tela de auditoria listando todo o histórico de interações daquele usuário.
3. **Sistema:** Apresenta dados como: horário de logins efetuados, registros de importação de arquivos, registros de exportação/downloads e outras ações rastreáveis.

---

### 3.3 Auditoria e Rastreabilidade (Logs)

O sistema registra e disponibiliza na interface os seguintes marcos operacionais:

* Data e hora exata da Autenticação (Login);
* Ações de execução de Criptografia;
* Ações de execução de Descriptografia;
* Operações de arquivos (Upload via Importar / Download automático).

---

### 3.4 Encerramento da Sessão

1. O **Usuário** clica no botão "Sair" a partir da tela Home (ou encerra a aba do navegador).
2. O **Sistema** invalida a sessão ativa.
3. O **Sistema** retorna a navegação para a tela inicial de **Login**.

---