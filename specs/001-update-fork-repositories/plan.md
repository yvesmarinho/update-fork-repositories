# Implementation Plan: Sincronização de Repositórios Fork com Upstream

**Branch**: `001-update-fork-repositories` | **Date**: 05/08/2026 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-update-fork-repositories/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Ferramenta CLI em Python (somente biblioteca padrão) que lê uma configuração
JSON com uma lista de repositórios git locais (forks) e, para cada um, traz
as atualizações do repositório `upstream` já configurado no `.git` local
(`fetch` → fast-forward merge → `push` para `origin`). Execução single-shot,
pensada para ser chamada por `cron`/`systemd timer`. Falha em um repositório
não interrompe o processamento dos demais; o código de saída do processo
reflete o sucesso agregado. Instalação: executável em `~/.local/bin/`,
configuração default em `~/.config/update-fork-repositories/config.json`.

## Technical Context

**Language/Version**: Python 3.12+ (gerenciado por `uv`, conforme ambiente do projeto)

**Primary Dependencies**: Nenhuma dependência externa — apenas biblioteca
padrão (`argparse`, `json`, `logging`, `subprocess`, `pathlib`, `dataclasses`,
`sys`). Chamadas git via `subprocess` (sem GitPython/PyGithub).

**Storage**: N/A — sem persistência própria; estado é o próprio repositório
git em disco (`.git` de cada fork).

**Testing**: `pytest`, com mocks de `subprocess`/filesystem para os testes
unitários e um cenário de integração com repositórios git reais criados em
diretório temporário (`tmp_path`).

**Target Platform**: Linux (ambiente do usuário), CLI invocada manualmente ou
por `cron`/`systemd timer`.

**Project Type**: CLI / script utilitário single-shot (não é serviço
long-running, não expõe API).

**Performance Goals**: Não crítico — execução batch diária; tempo dominado
pela latência de rede do `git fetch`/`push` por repositório. Sem meta de
throughput específica.

**Constraints**: Sem dependências de terceiros (stdlib apenas); sem tokens
ou segredos em texto (autenticação via SSH já configurado); nunca mesclar
histórico divergente automaticamente; falha em um repositório não pode
interromper os demais (graceful degradation).

**Scale/Scope**: Dezenas de repositórios fork por execução (uso pessoal do
usuário) — sem necessidade de paralelismo/concorrência nesta fase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md` ainda está no template padrão (placeholders
não preenchidos) — não há constitution específica do projeto ratificada.
Na ausência dela, este plano segue as regras globais do usuário aplicáveis a
projetos Python (`~/.claude/CLAUDE.md`, `~/.claude/rules/python.md`) e o
`CLAUDE.md` do repositório:

- ✅ **Bibliotecas padrão / `uv`**: sem dependências externas de runtime;
  `uv` gerencia ambiente/dependências de desenvolvimento (pytest, ruff, mypy).
- ✅ **Camadas (DDD leve / Ports & Adapters simplificado)**: Presentation
  (CLI/argparse) → Application (orquestração da lista de repositórios) →
  Domain (regras de sincronização, sem dependência de `subprocess`) →
  Infrastructure (adapter git via `subprocess`, leitura de config JSON).
- ✅ **Tratamento de erros por camada**: Domain/Infrastructure levantam
  exceções específicas; Application converte em `ResultadoSincronizacao`
  por repositório; Presentation converte o agregado em exit code.
- ✅ **Logging obrigatório, nunca `print`**: logging estruturado conforme
  regra global.
- ✅ **Testes por camada, cobertura mínima 90%**: unit (domain/application
  com mocks do adapter git) + integration (adapter git contra repositórios
  reais em `tmp_path`).
- **Gate status**: PASS — nenhuma violação a justificar em
  "Complexity Tracking".

## Project Structure

### Documentation (this feature)

```text
specs/001-update-fork-repositories/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
├── contracts/             # Phase 1 output (/speckit-plan command)
│   └── cli.md
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/update_fork_repositories/
├── __init__.py
├── __main__.py            # entrypoint (permite `python -m update_fork_repositories`)
├── cli.py                 # Presentation: argparse, monta config, chama application, define exit code
├── domain/
│   ├── __init__.py
│   ├── models.py           # RepositorioConfig, ResultadoSincronizacao, StatusSincronizacao (enum)
│   └── exceptions.py        # exceções específicas (RepositorioInvalidoError, UpstreamAusenteError, etc.)
├── application/
│   ├── __init__.py
│   └── sincronizar_forks.py # orquestra: lê config → para cada repo chama o adapter → agrega resultados
└── infrastructure/
    ├── __init__.py
    ├── config_loader.py      # lê/valida ~/.config/update-fork-repositories/config.json
    └── git_adapter.py        # subprocess: fetch, status --porcelain, merge --ff-only, stash, push

tests/
├── unit/
│   ├── test_models.py
│   ├── test_config_loader.py
│   └── test_sincronizar_forks.py   # application com git_adapter mockado
└── integration/
    └── test_git_adapter.py         # repositórios git reais em tmp_path
```

**Structure Decision**: Projeto single (Option 1), sem frontend/backend
separados — é um script CLI. Estrutura em camadas dentro de
`src/update_fork_repositories/` (`domain/` sem dependências externas,
`infrastructure/` isola `subprocess`/filesystem, `application/` orquestra,
`cli.py` é a única camada que conhece `argparse`/exit codes). Instalação via
entry point do `pyproject.toml` apontando para `cli:main`, publicado em
`~/.local/bin/update-fork-repositories` (`pip install --user` / `uv tool
install`, a definir na fase de tasks).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Nenhuma violação — seção não aplicável.
