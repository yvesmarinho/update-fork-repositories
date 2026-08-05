# Feature Specification: Sincronização de Repositórios Fork com Upstream

**Feature Branch**: `001-update-fork-repositories`

**Created**: 05/08/2026

**Status**: Draft

**Input**: User description: "Script daemon Python (biblioteca padrão apenas) que lê um JSON de configuração listando pastas de repositórios fork locais e, para cada um, traz as atualizações do repositório upstream (origem do fork), fazendo fetch + fast-forward merge + push. Executável instalado em ~/.local/bin/; JSON de configuração default em ~/.config/update-fork-repositories/config.json. Execução single-shot via cron/systemd. Cada repositório no JSON tem apenas o campo \"path\" (dados de git como upstream/origin/branch são lidos do próprio .git local) e um campo opcional \"on_dirty_working_tree\" (\"abort\" default | \"stash\") controlando o comportamento quando há mudanças locais não commitadas. Falha em um repositório não interrompe o processamento dos demais; exit code 0 apenas se todos sincronizarem com sucesso."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sincronizar todos os forks em uma execução (Priority: P1)

Como dono de vários repositórios fork no GitHub, quero que, ao rodar o
comando, todos os forks listados na minha configuração sejam atualizados
com as mudanças do repositório original (upstream), sem precisar entrar em
cada pasta manualmente.

**Why this priority**: É o valor central do produto — sem isso não há
motivo para o projeto existir. É o MVP.

**Independent Test**: Pode ser testado configurando 2-3 repositórios locais
com um remote `upstream` desatualizado em relação ao remoto, rodando o
comando, e verificando que a branch local e o `origin` (fork remoto) ficam
com o mesmo HEAD do `upstream`.

**Acceptance Scenarios**:

1. **Given** um repositório fork local com working tree limpa e branch
   atrasada em relação ao `upstream`, **When** o comando é executado,
   **Then** a branch local avança por fast-forward até o HEAD do `upstream`
   e o `origin` (fork remoto) recebe o mesmo commit via push.
2. **Given** um repositório fork local já sincronizado com o `upstream`,
   **When** o comando é executado, **Then** nenhuma alteração é feita e o
   repositório é reportado como sem mudanças.
3. **Given** dois repositórios na configuração, um sincroniza com sucesso e
   outro falha (ex.: sem remote `upstream`), **When** o comando é
   executado, **Then** o primeiro é atualizado normalmente e o segundo é
   reportado como falha, sem interromper o processamento do primeiro.

---

### User Story 2 - Não perder trabalho local não commitado (Priority: P2)

Como usuário que às vezes deixa mudanças não commitadas em um fork, quero
controlar por repositório o que acontece quando há mudanças pendentes, para
não correr o risco de perder trabalho em progresso durante a sincronização
automática.

**Why this priority**: Protege contra perda de dados — crítico para
confiança no uso diário/automatizado da ferramenta, mas depende do fluxo
básico (User Story 1) já funcionar.

**Independent Test**: Pode ser testado deixando um arquivo modificado sem
commit em um dos repositórios configurados, rodando o comando com cada
configuração de `on_dirty_working_tree`, e observando o comportamento
resultante (working tree preservado intacto vs. stash/pop aplicado).

**Acceptance Scenarios**:

1. **Given** um repositório com mudanças não commitadas e
   `on_dirty_working_tree` não definido (default), **When** o comando é
   executado, **Then** o repositório é reportado como pendente/sujo e
   nenhuma operação de sincronização é feita nele, preservando as
   mudanças locais exatamente como estavam.
2. **Given** um repositório com mudanças não commitadas e
   `on_dirty_working_tree` configurado para preservar via stash
   temporário, **When** o comando é executado, **Then** o repositório é
   sincronizado com o `upstream` e as mudanças locais são restauradas ao
   final.
3. **Given** um repositório configurado para stash temporário, **When** a
   restauração das mudanças locais falha após a sincronização (conflito),
   **Then** o repositório é reportado como falha e as mudanças locais
   continuam preservadas (não descartadas) para o usuário resolver
   manualmente.

---

### User Story 3 - Rodar automaticamente todo dia sem intervenção (Priority: P3)

Como usuário que quer manter os forks sempre atualizados sem lembrar de
fazer isso manualmente, quero poder agendar a execução diária do comando
através do agendador do meu sistema operacional, e poder verificar
facilmente se a última execução teve sucesso ou falha.

**Why this priority**: Valor de conveniência/automação — depende das
Stories 1 e 2 já funcionarem corretamente antes de fazer sentido agendar.

**Independent Test**: Pode ser testado agendando o comando via cron/systemd
timer, verificando nos dias seguintes que o log mostra execuções diárias e
que o código de saída do processo reflete corretamente sucesso ou falha
agregada.

**Acceptance Scenarios**:

1. **Given** o comando está agendado para rodar diariamente, **When** todas
   as sincronizações da execução têm sucesso, **Then** o processo termina
   com código de saída de sucesso, permitindo que o agendador não dispare
   alertas de falha.
2. **Given** pelo menos um repositório falha durante a execução agendada,
   **When** o processo termina, **Then** o código de saída indica falha,
   permitindo que o agendador (cron/systemd) detecte e notifique o
   problema por seus próprios mecanismos.

---

### Edge Cases

- O que acontece quando o caminho (`path`) informado na configuração não
  existe ou não é um repositório git? → Repositório é reportado como falha
  (erro de configuração), demais repositórios continuam sendo processados.
- O que acontece quando o repositório não tem um remote `upstream`
  configurado? → Repositório é reportado como falha, sem tentativa de
  inferir ou criar automaticamente a URL do upstream.
- O que acontece quando o histórico local diverge do `upstream` (não é
  possível fast-forward)? → Repositório é reportado como divergente/falha;
  nenhuma tentativa automática de merge com resolução de conflitos é feita.
- O que acontece quando o arquivo de configuração JSON está ausente ou é
  inválido? → O processo falha imediatamente, antes de processar qualquer
  repositório (fail fast), com mensagem indicando o problema.
- O que acontece se não houver conectividade de rede para alcançar o
  `upstream` ou o `origin`? → Repositório é reportado como falha; os demais
  repositórios continuam sendo processados normalmente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE ler o caminho do arquivo de configuração via
  argumento de linha de comando; se omitido, DEVE usar como padrão
  `~/.config/update-fork-repositories/config.json`.
- **FR-002**: O sistema DEVE validar a estrutura da configuração antes de
  processar qualquer repositório, falhando imediatamente se ela for
  inválida ou o arquivo não existir.
- **FR-003**: Para cada repositório listado, o sistema DEVE buscar as
  atualizações do remote `upstream` já configurado no repositório local.
- **FR-004**: O sistema DEVE aplicar apenas avanço rápido (fast-forward) ao
  incorporar mudanças do `upstream`; histórico divergente NÃO deve ser
  mesclado automaticamente.
- **FR-005**: Após incorporar as mudanças do `upstream` com sucesso, o
  sistema DEVE enviar (push) o resultado para o remote `origin` (o fork no
  GitHub).
- **FR-006**: A falha ao processar um repositório NÃO DEVE interromper o
  processamento dos demais repositórios da lista.
- **FR-007**: O sistema DEVE registrar (log) o resultado do processamento
  de cada repositório de forma individual e identificável.
- **FR-008**: O processo DEVE encerrar com código de saída de sucesso
  apenas se todos os repositórios foram processados sem falha; caso
  contrário, DEVE encerrar com código de saída de falha.
- **FR-009**: O sistema DEVE respeitar, por repositório, uma configuração
  que determina o comportamento diante de mudanças locais não commitadas:
  abortar aquele repositório sem alterá-lo (comportamento padrão), ou
  preservar temporariamente as mudanças (stash) durante a sincronização e
  restaurá-las ao final.
- **FR-010**: Se o remote `upstream` não existir no repositório local, o
  sistema DEVE reportar aquele repositório como falha, sem tentar criar o
  remote automaticamente.
- **FR-011**: O executável instalado DEVE poder ser chamado diretamente
  pelo `PATH` do usuário (instalado em `~/.local/bin/`).

### Key Entities

- **Repositório Configurado**: representa um fork local a ser sincronizado.
  Atributos: caminho da pasta local; política de tratamento de mudanças não
  commitadas (abortar ou preservar temporariamente).
- **Resultado de Sincronização**: representa o desfecho do processamento de
  um repositório em uma execução. Atributos: identificação do repositório,
  status (sucesso sem mudanças, sucesso com atualização, pendência de
  mudanças locais, divergência de histórico, ou erro), detalhe/mensagem,
  momento da execução.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Após uma execução bem-sucedida, 100% dos repositórios
  configurados com working tree limpa e sem divergência de histórico ficam
  com a branch local e o fork remoto (`origin`) idênticos ao HEAD do
  `upstream`.
- **SC-002**: Uma falha em um repositório específico não reduz a taxa de
  sucesso dos demais repositórios da mesma execução — os demais continuam
  sendo sincronizados normalmente.
- **SC-003**: O código de saída do processo permite, sem inspecionar o
  conteúdo do log, distinguir uma execução 100% bem-sucedida de uma
  execução com pelo menos uma falha — verificável por qualquer agendador
  externo (cron/systemd).
- **SC-004**: Mudanças locais não commitadas em um repositório configurado
  para o comportamento padrão nunca são alteradas ou perdidas por uma
  execução do comando.
- **SC-005**: Um repositório configurado para preservar mudanças locais
  temporariamente mantém essas mudanças intactas mesmo quando a
  restauração após a sincronização falha (nada é descartado).

## Assumptions

- Cada repositório listado na configuração já é um clone git local válido,
  com o remote `origin` apontando para o fork no GitHub e o remote
  `upstream` já configurado apontando para o repositório de origem —
  configuração feita manualmente pelo usuário uma vez, na criação do fork.
- O acesso de rede necessário para `fetch`/`push` (ex.: chave SSH) já está
  configurado no ambiente onde o comando roda.
- O agendamento diário (ex.: cron, systemd timer) é responsabilidade do
  usuário/ambiente, fora do escopo desta funcionalidade — o comando apenas
  precisa se comportar de forma correta ao ser executado uma vez.
- Resolução automática de conflitos de merge está fora de escopo desta
  fase; repositórios com histórico divergente são apenas reportados.
- Descoberta automática de forks via API do GitHub, notificações externas
  (e-mail/Slack) e interface interativa estão fora de escopo desta fase.
