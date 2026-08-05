---

description: "Task list for feature implementation"
---

# Tasks: Sincronização de Repositórios Fork com Upstream

**Input**: Design documents from `/specs/001-update-fork-repositories/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluídas — regras globais do projeto (`~/.claude/rules/python.md`) exigem cobertura mínima de 90% via `pytest`.

**Organization**: Tarefas agrupadas por user story (US1, US2, US3 de `spec.md`), com Setup e Foundational compartilhados antes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**: US1, US2 ou US3, mapeado de `spec.md`
- Caminhos de arquivo exatos em cada descrição

## Path Conventions

Projeto single (Option 1), conforme `plan.md`: `src/update_fork_repositories/`, `tests/unit/`, `tests/integration/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialização do projeto Python e ferramentas de qualidade.

- [X] T001 Configurar `pyproject.toml` (raiz do repo): `requires-python = ">=3.12"`, metadados do pacote, `[project.scripts]` `update-fork-repositories = "update_fork_repositories.cli:main"`
- [X] T002 [P] Adicionar dependências de desenvolvimento via `uv add --dev pytest pytest-cov ruff mypy` (atualiza `pyproject.toml`/`uv.lock`)
- [X] T003 [P] Configurar `ruff` e `mypy` em `pyproject.toml` (seções `[tool.ruff]`, `[tool.mypy]`) conforme regras globais (`strict typing`, lint)
- [X] T004 Criar estrutura de pastas vazias com `__init__.py` em `src/update_fork_repositories/domain/`, `src/update_fork_repositories/application/`, `src/update_fork_repositories/infrastructure/`, `tests/unit/`, `tests/integration/`

**Checkpoint**: `uv sync`, `uv run ruff check .` e `uv run pytest` (sem testes ainda) rodam sem erro de configuração.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Modelos de domínio, exceções e infraestrutura de logging/config compartilhados por todas as user stories — nenhuma story pode ser implementada antes desta fase.

**⚠️ CRITICAL**: Bloqueia todas as user stories.

- [X] T005 [P] Criar enum `StatusSincronizacao` e dataclasses `RepositorioConfig`, `ResultadoSincronizacao` em `src/update_fork_repositories/domain/models.py`, conforme `data-model.md` (type hints, sem dependências externas)
- [X] T006 [P] Criar exceções `RepositorioInvalidoError`, `UpstreamAusenteError`, `ComandoGitFalhouError`, `ConfiguracaoInvalidaError` em `src/update_fork_repositories/domain/exceptions.py`
- [X] T007 Configurar logging estruturado (função `config_logging()` conforme padrão global) em `src/update_fork_repositories/cli.py`
- [X] T008 [P] Unit test de `RepositorioConfig`/`ResultadoSincronizacao`/`StatusSincronizacao` (validação de campos, defaults) em `tests/unit/test_models.py`

**Checkpoint**: Modelos e exceções de domínio testados e prontos; `uv run pytest tests/unit/test_models.py` passa.

---

## Phase 3: User Story 1 - Sincronizar todos os forks em uma execução (Priority: P1) 🎯 MVP

**Goal**: Rodar o comando processa todos os repositórios do JSON de config, trazendo fetch + fast-forward merge + push do `upstream`, sem interromper os demais em caso de falha isolada.

**Independent Test**: Configurar 2-3 repositórios locais (um deles sem `upstream`) conforme `quickstart.md` (Cenários 1, 2 e 4), rodar o comando, e verificar status/exit code por repositório.

### Tests for User Story 1 ⚠️

> Escrever estes testes PRIMEIRO; garantir que falham antes da implementação.

- [X] T009 [P] [US1] Unit test do `config_loader` (JSON válido, ausente, malformado) em `tests/unit/test_config_loader.py`
- [X] T010 [P] [US1] Unit test de `sincronizar_forks` (orquestração) com `git_adapter` mockado — casos `OK`, `NO_CHANGES`, `ERROR` isolado não bloqueia os demais — em `tests/unit/test_sincronizar_forks.py`
- [X] T011 [P] [US1] Integration test do `git_adapter` com repositórios git reais em `tmp_path` (fetch, fast-forward, push, detecção de divergência) em `tests/integration/test_git_adapter.py`

### Implementation for User Story 1

- [X] T012 [US1] Implementar `infrastructure/config_loader.py`: ler e validar o JSON (schema de `contracts/config.schema.json`), levantando `ConfiguracaoInvalidaError` em caso de estrutura inválida (depende de T005, T006)
- [X] T013 [US1] Implementar `infrastructure/git_adapter.py`: (a) validar que `path` existe e contém `.git`, levantando `RepositorioInvalidoError` caso contrário (FR — edge case "path inválido"); (b) validar que o remote `upstream` existe (`git remote get-url upstream`), levantando `UpstreamAusenteError` caso contrário, sem tentar criá-lo (FR-010); (c) funções via `subprocess` para `fetch`, `rev-list --left-right --count` (detectar fast-forward vs. divergência), `merge --ff-only`, `push` (depende de T006)
- [X] T013a [P] [US1] Unit test cobrindo `RepositorioInvalidoError` (path inexistente/sem `.git`) e `UpstreamAusenteError` (remote `upstream` ausente) em `tests/unit/test_git_adapter_validacao.py` (depende de T006, T013) — cobre FR-010 e o edge case de path inválido
- [X] T014 [US1] Implementar `application/sincronizar_forks.py`: para cada `RepositorioConfig`, chamar o `git_adapter`, capturar exceções de domínio e produzir `ResultadoSincronizacao`, agregando a lista final (depende de T012, T013)
- [X] T015 [US1] Implementar `cli.py` (`main()`): parse de argumento posicional opcional `CONFIG_PATH` (default `~/.config/update-fork-repositories/config.json`), chamar `sincronizar_forks`, logar cada resultado, calcular e retornar exit code (depende de T007, T014)
- [X] T016 [US1] Adicionar tratamento de erro fail-fast na CLI para `ConfiguracaoInvalidaError` (log nível ERROR, exit code 1, sem processar repositórios) em `src/update_fork_repositories/cli.py`

**Checkpoint**: User Story 1 funcional e testável de forma independente — `uv run pytest tests/unit tests/integration -k "not stash"` passa; Cenários 1, 2 e 4 de `quickstart.md` funcionam manualmente.

---

## Phase 4: User Story 2 - Não perder trabalho local não commitado (Priority: P2)

**Goal**: Respeitar `on_dirty_working_tree` por repositório (`"abort"` default | `"stash"`), nunca perdendo mudanças locais não commitadas.

**Independent Test**: Cenário 3 de `quickstart.md` — deixar mudança não commitada em um repositório, rodar com cada configuração de `on_dirty_working_tree`, verificar working tree preservado/restaurado.

### Tests for User Story 2 ⚠️

- [X] T017 [P] [US2] Unit test de `sincronizar_forks` para status `DIRTY` (default `"abort"`, sem alterar o repositório) em `tests/unit/test_sincronizar_forks.py`
- [X] T018 [P] [US2] Integration test do `git_adapter` para `stash`/`stash pop` com sucesso e com falha no `pop` (stash preservado) em `tests/integration/test_git_adapter.py`

### Implementation for User Story 2

- [X] T019 [US2] Implementar detecção de working tree suja (`git status --porcelain`) em `src/update_fork_repositories/infrastructure/git_adapter.py` (depende de T013)
- [X] T020 [US2] Implementar `stash push`/`stash pop` no `git_adapter`, preservando o stash (sem `drop`) quando o `pop` falhar, em `src/update_fork_repositories/infrastructure/git_adapter.py` (depende de T019)
- [X] T021 [US2] Integrar a política `on_dirty_working_tree` (`"abort"` → status `DIRTY`; `"stash"` → stash/pop ao redor do fetch+merge+push) em `src/update_fork_repositories/application/sincronizar_forks.py` (depende de T014, T020)
- [X] T022 [US2] Validar `on_dirty_working_tree` no `config_loader.py` (apenas `"abort"`/`"stash"` aceitos, senão `ConfiguracaoInvalidaError`) em `src/update_fork_repositories/infrastructure/config_loader.py` (depende de T012)

**Checkpoint**: User Stories 1 e 2 funcionam de forma independente e combinada — Cenário 3 de `quickstart.md` passa nos dois modos.

---

## Phase 5: User Story 3 - Rodar automaticamente todo dia sem intervenção (Priority: P3)

**Goal**: Instalar o comando em `~/.local/bin/` e permitir agendamento via cron/systemd, com exit code confiável para automação.

**Independent Test**: Instalar via `uv tool install .`, agendar uma execução via `cron`/`systemd timer` (ou simular chamando o comando duas vezes seguidas), e confirmar que o exit code reflete corretamente sucesso/falha agregados, sem interação manual.

### Tests for User Story 3 ⚠️

- [X] T023 [P] [US3] Unit test do exit code agregado da CLI (todos `OK`/`NO_CHANGES` → 0; qualquer `DIRTY`/`DIVERGED`/`ERROR` → != 0) em `tests/unit/test_cli.py`

### Implementation for User Story 3

- [X] T024 [US3] Garantir que `cli.py` resolve o default `~/.config/update-fork-repositories/config.json` via `pathlib.Path.home()` quando `CONFIG_PATH` for omitido (depende de T015)
- [X] T025 [P] [US3] Criar exemplo de unit de systemd (`update-fork-repositories.service` + `.timer`, execução diária) em `specs/001-update-fork-repositories/contracts/systemd/`, conforme referenciado em `contracts/cli.md` — apenas documentação/exemplo, não executado pelo pacote
- [X] T026 [US3] Documentar instalação (`uv tool install .`) e agendamento (cron/systemd) em `README.md`, referenciando `contracts/cli.md`

**Checkpoint**: Todas as user stories funcionam de forma independente; comando instalável e agendável conforme `spec.md` (User Story 3).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Qualidade final e validação end-to-end.

- [X] T027 [P] Rodar `uv run ruff check .` e `uv run mypy src/` e corrigir achados em todo `src/update_fork_repositories/`
- [X] T028 [P] Conferir cobertura de testes ≥ 90% com `uv run pytest --cov=update_fork_repositories --cov-report=term-missing`
- [X] T029 Executar manualmente os 4 cenários de `specs/001-update-fork-repositories/quickstart.md` de ponta a ponta
- [X] T030 [P] Atualizar `docs/TODO.md` marcando os itens desta feature como concluídos, preservando o histórico existente

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências — pode iniciar imediatamente
- **Foundational (Phase 2)**: depende do Setup — bloqueia todas as user stories
- **User Story 1 (Phase 3)**: depende do Foundational — é o MVP
- **User Story 2 (Phase 4)**: depende do Foundational; integra-se ao fluxo de US1 (mesmos arquivos `git_adapter.py`/`sincronizar_forks.py`), mas é testável isoladamente pelos cenários de working tree suja
- **User Story 3 (Phase 5)**: depende do Foundational e do `cli.py` de US1 (T015); não depende de US2
- **Polish (Phase 6)**: depende de todas as user stories desejadas estarem completas

### User Story Dependencies

- **US1 (P1)**: sem dependência de outras stories
- **US2 (P2)**: reaproveita arquivos criados por US1 (`git_adapter.py`, `sincronizar_forks.py`, `config_loader.py`) — implementar depois de US1 por reduzir conflito de merge, mas continua independentemente testável (Cenário 3 do quickstart)
- **US3 (P3)**: reaproveita `cli.py` de US1; independente de US2

### Within Each User Story

- Testes escritos e falhando antes da implementação
- Modelos/infra antes de application
- Application antes de CLI
- Story completa antes de avançar para a próxima prioridade

### Parallel Opportunities

- T002, T003 (Setup) em paralelo
- T005, T006, T008 (Foundational) em paralelo
- T009, T010, T011 (testes de US1) em paralelo entre si
- T017, T018 (testes de US2) em paralelo entre si
- T027, T028, T030 (Polish) em paralelo entre si

---

## Parallel Example: User Story 1

```bash
# Testes de US1 em paralelo:
Task: "Unit test do config_loader em tests/unit/test_config_loader.py"
Task: "Unit test de sincronizar_forks (mock do git_adapter) em tests/unit/test_sincronizar_forks.py"
Task: "Integration test do git_adapter em tests/integration/test_git_adapter.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Phase 1: Setup
2. Completar Phase 2: Foundational (bloqueia as demais)
3. Completar Phase 3: User Story 1
4. **PARAR e VALIDAR**: rodar Cenários 1, 2 e 4 de `quickstart.md`
5. Instalar localmente (`uv tool install .`) e usar no dia a dia se desejado

### Incremental Delivery

1. Setup + Foundational → base pronta
2. US1 → validar independentemente → já é utilizável manualmente (MVP)
3. US2 → validar independentemente (Cenário 3) → protege contra perda de trabalho
4. US3 → validar independentemente → habilita agendamento automático diário
5. Cada story agrega valor sem quebrar as anteriores

---

## Notes

- [P] = arquivos diferentes, sem dependência pendente
- [Story] mapeia a tarefa à user story correspondente em `spec.md`
- Cada user story deve ser completável e testável de forma independente
- Verificar que os testes falham antes de implementar (TDD)
- Rodar `uv run ruff check .` e `uv run pytest` antes de cada commit (regra global)
- Parar em qualquer checkpoint para validar a story isoladamente
