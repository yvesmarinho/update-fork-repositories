<!-- Criado em: 05/08/2026 09:13 -->
<!-- Modificado em: 05/08/2026 09:34 -->

# Especificação: update-fork-repositories

**Última atualização**: 05/08/2026
**Owner**: update-fork-repositories owner
**Status**: Draft — sem pendências de esclarecimento (todos os gates fechados)

## Visão Geral

Script Python (somente biblioteca padrão) que lê um arquivo JSON com a lista de
repositórios fork locais e, para cada um, traz as atualizações do repositório
de origem (upstream) — ou seja, sincroniza o fork local com o repositório do
qual ele foi criado. Pensado para execução única, disparada diariamente por um
agendador externo (`cron` ou `systemd timer`).

## Instalação e Localização

- **Executável**: o script/entrypoint instalado deve ficar em `~/.local/bin/`
  (ex.: `~/.local/bin/update-fork-repositories`), diretório padrão do `PATH`
  do usuário para binários locais — permite chamar o comando diretamente ou
  a partir de cron/systemd sem caminho completo.
- **Configuração**: o JSON de configuração deve ficar em uma pasta dedicada
  dentro de `~/.config/`, seguindo a convenção XDG (`~/.config/<nome-do-app>/`)
  — proposta: `~/.config/update-fork-repositories/config.json`.
- O script DEVE aceitar o caminho do JSON via argumento de linha de comando
  (FR-001) e, se omitido, usar o caminho default acima
  (`~/.config/update-fork-repositories/config.json`).

## Escopo

**Dentro do escopo**:
- Ler e validar o JSON de configuração.
- Para cada repositório: `git fetch` do upstream, merge/fast-forward na branch
  default local, `git push` para o `origin` (fork no GitHub).
- Continuar processando os demais repositórios mesmo se um falhar (graceful
  degradation — falha de um item é logada e agregada, não derruba a execução).
- Logging estruturado (stdlib `logging`) com resultado por repositório.
- Exit code do processo refletindo sucesso geral (`0`) ou falha parcial/total
  (`!= 0`) para uso por cron/systemd.

**Fora do escopo (nesta fase)**:
- Descoberta automática de forks via API do GitHub.
- Resolução automática de conflitos de merge.
- Interface web ou CLI interativa.
- Notificações externas (e-mail, Slack, etc.).
- Criação/autenticação de repositórios via API.

## Formato do JSON de Configuração

O JSON contém apenas o caminho da pasta de cada projeto; os demais dados
(remote `upstream`, remote `origin`, branch atual) são obtidos lendo o `.git`
do próprio repositório (`git remote`, `git branch --show-current`) — não são
duplicados no config.

```json
{
  "repositorios": [
    {
      "path": "/home/usuario/forks/algum-projeto",
      "on_dirty_working_tree": "abort"
    }
  ]
}
```

Campos:
- `path` (obrigatório): caminho absoluto da pasta do projeto (clone git local
  do fork). O script lê o remote `upstream` já configurado nesse `.git` — se
  esse remote não existir, o repositório é reportado como `ERROR`
  (`upstream remote não configurado`), sem inferir/criar URL automaticamente.
- `on_dirty_working_tree` (opcional, default `"abort"`): tratamento quando o
  repositório tem mudanças locais não commitadas. Valores aceitos:
  - `"abort"` (default): não mexe no working tree; reporta o repositório como
    `DIRTY` no log e segue para o próximo, sem sincronizar.
  - `"stash"`: executa `git stash` antes do fetch/merge e `git stash pop`
    logo depois; se o `pop` falhar (conflito ao restaurar o stash), reporta
    `ERROR` com o stash preservado (não descartado) para o usuário resolver
    manualmente.

**Pré-requisito**: cada repositório listado precisa ter um remote chamado
`upstream` já configurado localmente (`git remote add upstream <url>`), feito
uma vez pelo usuário na criação do fork — o script não cria remotes.

## Fluxo de Sincronização (por repositório)

1. Validar que `path` existe e é um repositório git válido (`.git` presente).
2. Ler do `.git` local: remote `upstream`, remote `origin`, branch atual
   (`HEAD`). Se o remote `upstream` não existir: reportar `ERROR` e passar
   para o próximo repositório.
3. Verificar se há mudanças não commitadas (`git status --porcelain`):
   - Se houver e `on_dirty_working_tree == "abort"`: reportar `DIRTY` e
     passar para o próximo repositório.
   - Se houver e `on_dirty_working_tree == "stash"`: `git stash`.
4. `git fetch upstream`.
5. Verificar se a branch local está atrás do upstream (`git rev-list`/
   `merge-base`).
6. Se atrasada: tentar fast-forward (`git merge --ff-only`).
   - Se o fast-forward falhar (histórico divergente): registrar como falha
     (`DIVERGED`) e **não** tentar merge automático de conflitos.
7. Se `on_dirty_working_tree == "stash"` foi aplicado no passo 3: `git stash
   pop`. Falha no pop → `ERROR`, stash mantido na pilha (não descartado).
8. Se o fast-forward teve sucesso: `git push origin <branch>`.
9. Registrar resultado (`OK`, `NO_CHANGES`, `DIRTY`, `DIVERGED`, `ERROR`) no
   log.

Uma falha em qualquer etapa de um repositório é capturada, logada com
detalhe, e o processamento segue para o próximo repositório da lista.

## Requisitos Funcionais

- **FR-001**: O sistema DEVE ler o caminho do JSON de configuração via
  argumento de linha de comando; se omitido, DEVE usar o default
  `~/.config/update-fork-repositories/config.json`.
- **FR-002**: O sistema DEVE validar a estrutura do JSON antes de processar
  qualquer repositório (fail fast em config inválida).
- **FR-003**: Para cada repositório, o sistema DEVE buscar (`fetch`) as
  atualizações do remote `upstream` já configurado no `.git` local.
- **FR-004**: O sistema DEVE aplicar apenas fast-forward merge; histórico
  divergente NÃO deve ser mesclado automaticamente.
- **FR-005**: Após merge bem-sucedido, o sistema DEVE fazer `push` para o
  remote `origin` (fork).
- **FR-006**: Falha em um repositório NÃO DEVE interromper o processamento
  dos demais.
- **FR-007**: O sistema DEVE logar (via `logging`, nunca `print`) o resultado
  de cada repositório processado.
- **FR-008**: O processo DEVE retornar exit code `0` somente se todos os
  repositórios foram sincronizados com sucesso (`OK` ou `NO_CHANGES`).
- **FR-009**: O sistema DEVE respeitar o campo `on_dirty_working_tree` de
  cada repositório (`"abort"` ou `"stash"`) ao encontrar mudanças locais não
  commitadas.
- **FR-010**: Se o remote `upstream` não existir no repositório, o sistema
  DEVE reportar `ERROR` para aquele repositório sem tentar criá-lo.

### Key Entities

- **RepositorioConfig**: entrada do JSON — `path` (obrigatório),
  `on_dirty_working_tree` (opcional, `"abort"` | `"stash"`, default
  `"abort"`).
- **ResultadoSincronizacao**: resultado por repositório — status
  (`OK`/`NO_CHANGES`/`DIRTY`/`DIVERGED`/`ERROR`), mensagem, timestamp.

## Autenticação

Autenticação via chave SSH já configurada no ambiente de execução do usuário
(sem tokens/segredos no JSON de configuração ou no código-fonte, conforme
regras globais de segurança do usuário).

## Não-Funcionais

- **Confiabilidade**: execução batch, sem SLA de disponibilidade; idempotente
  (rodar novamente sem alterações pendentes resulta em `NO_CHANGES`).
- **Segurança**: sem segredos em texto; validação de entrada (paths e URLs)
  nas fronteiras.
- **Manutenibilidade**: cobertura de testes alvo 90%, type hints, lint via
  `ruff`, tipagem via `mypy`, docstrings reStructuredText.
- **Portabilidade**: Linux (ambiente do usuário), Python 3.12+, dependência
  externa única: binário `git` no PATH.

## Critérios de Sucesso (Measurable Outcomes)

- **SC-001**: Executar o script com N repositórios no JSON resulta em N
  entradas de log, uma por repositório, com status individual.
- **SC-002**: Um repositório com histórico divergente é reportado como
  `DIVERGED` sem abortar o processamento dos demais.
- **SC-003**: Exit code `0` quando todos os repositórios retornam `OK` ou
  `NO_CHANGES`; exit code `!= 0` caso contrário — compatível com verificação
  de sucesso em cron/systemd (`OnFailure=`, alertas de e-mail do cron, etc.).
- **SC-004**: Um repositório com `on_dirty_working_tree: "abort"` e mudanças
  locais não commitadas é reportado como `DIRTY`, sem alterar o working tree.
- **SC-005**: Um repositório com `on_dirty_working_tree: "stash"` sincroniza
  com sucesso e restaura as mudanças locais via `stash pop` ao final.

## Decisões Confirmadas (gates fechados)

Todos os pontos anteriormente marcados `[NEEDS CLARIFICATION]` foram
resolvidos:

1. **Campos do JSON**: apenas `path` por repositório; dados de git (remote
   `upstream`/`origin`, branch) são lidos do próprio `.git`, não duplicados
   no config.
2. **Modelo de execução**: single-shot, disparado por `cron`/`systemd timer`
   externo (confirmado).
3. **Working tree suja**: controlado por campo `on_dirty_working_tree` por
   repositório (`"abort"` default | `"stash"`), documentado acima.

## Assumptions

- Cada repositório listado já é um clone git local válido, com o remote
  `origin` apontando para o fork no GitHub e o remote `upstream` já
  configurado apontando para o repositório de origem.
- SSH já está configurado para push autenticado no fork.
- Ambiente de execução tem `git` instalado e acessível no PATH.
- Agendamento diário fica a cargo de `cron`/`systemd timer` externo ao script.
- `~/.local/bin` já está no `PATH` do usuário (padrão em distros modernas com
  XDG Base Directory habilitado).
