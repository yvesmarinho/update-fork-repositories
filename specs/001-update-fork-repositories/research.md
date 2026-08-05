# Research: Sincronização de Repositórios Fork com Upstream

Nenhum marcador `NEEDS CLARIFICATION` restou no Technical Context do
`plan.md` — todas as decisões relevantes já haviam sido fechadas nas fases
anteriores (`docs/architecture/spec-update-fork-repositories.md`,
`objetivo.yaml`, `spec.md`). Este documento registra as decisões técnicas
tomadas para a fase de design, com racional e alternativas consideradas.

## 1. Mecanismo de sincronização git

- **Decision**: Chamar o binário `git` via `subprocess.run` (stdlib), com
  `check=True`/tratamento explícito de `CalledProcessError`, capturando
  stdout/stderr para logging.
- **Rationale**: Atende à restrição "bibliotecas padrão" do usuário; `git`
  via subprocess é comportamento idêntico ao uso manual do usuário, sem
  reimplementar protocolo git; evita dependências como GitPython/PyGithub.
- **Alternatives considered**:
  - *GitPython*: mais ergonômico, mas é dependência externa — descartado
    por violar a restrição de bibliotecas padrão.
  - *PyGithub / API REST do GitHub (`merge-upstream`)*: sincroniza via API,
    sem precisar de clone local, mas exige token de autenticação (violaria
    a regra de nunca ter segredos em texto/código) e não serve para forks
    que não sejam do GitHub — descartado.

## 2. Detecção de fast-forward vs. divergência

- **Decision**: Após `git fetch upstream`, comparar `git rev-list
  --left-right --count <branch>...upstream/<branch>`; se a contagem à
  esquerda (commits locais não no upstream) for 0, é fast-forward seguro
  (`git merge --ff-only`); caso contrário, reportar `DIVERGED` sem tentar
  merge.
- **Rationale**: `--ff-only` já falha com erro claro em caso de divergência,
  mas fazer a checagem prévia permite reportar `DIVERGED` como status de
  negócio (não como exceção de infraestrutura), mantendo Domain/Application
  desacoplados de detalhes de git.
- **Alternatives considered**: Confiar apenas no exit code de `git merge
  --ff-only` e mapear falha genérica para `DIVERGED` — mais simples, porém
  mistura "falha de execução" com "divergência esperada de negócio"; a
  checagem prévia foi preferida para logging mais preciso.

## 3. Tratamento de working tree suja (`on_dirty_working_tree`)

- **Decision**: Verificar `git status --porcelain` antes de qualquer
  operação. Se houver saída (mudanças pendentes):
  - `"abort"` (default): reportar `DIRTY`, não tocar no repositório.
  - `"stash"`: `git stash push` antes do fetch/merge; `git stash pop`
    depois do push; se o `pop` falhar, reportar `ERROR` mantendo o stash
    na pilha (nunca `git stash drop`).
- **Rationale**: Atende à FR-009/SC-004/SC-005 já definidas na spec — nunca
  perder trabalho do usuário; op-in explícito por repositório via config.
- **Alternatives considered**: Stash automático sempre (sem opção) —
  rejeitado por escolha explícita do usuário na fase de especificação
  (risco de mascarar mudanças esquecidas). Abortar sempre (sem opção de
  stash) — rejeitado por reduzir a automação útil para repositórios onde o
  usuário sabe que quer preservar/restaurar mudanças locais.

## 4. Estrutura de camadas (DDD leve / Ports & Adapters)

- **Decision**: `domain` (modelos + exceções, sem I/O), `infrastructure`
  (adapter git via subprocess, leitor de config JSON), `application`
  (orquestra a lista de repositórios chamando o adapter, agrega
  resultados), `cli` (Presentation: argparse, logging setup, exit code).
- **Rationale**: Exigência das regras globais do usuário (arquitetura em
  camadas obrigatória, mesmo em projetos pequenos); permite testar a lógica
  de decisão (fast-forward vs. divergente, política de working tree) sem
  spawnar processos git reais (mock do adapter).
- **Alternatives considered**: Script único (`main.py` monolítico) — mais
  rápido de escrever, mas violaria a regra de modularidade obrigatória e
  dificultaria testes unitários isolados de git real.

## 5. Instalação em `~/.local/bin` e config em `~/.config`

- **Decision**: Entry point (`[project.scripts]` no `pyproject.toml`)
  apontando para `update_fork_repositories.cli:main`; instalação via
  `uv tool install .` ou `pip install --user .`, que publica o executável
  em `~/.local/bin/`. Config default lida de
  `~/.config/update-fork-repositories/config.json` (convenção XDG), com
  override via argumento posicional/`--config`.
- **Rationale**: Já decidido na fase de especificação; `uv tool install` é
  o mecanismo padrão do `uv` (ferramenta já adotada no projeto) para expor
  CLIs em `~/.local/bin` sem poluir o Python global.
- **Alternatives considered**: Script solto copiado manualmente para
  `~/.local/bin` — funciona, mas não versiona a instalação nem atualiza
  automaticamente com `uv tool upgrade`; preterido em favor do entry point
  packaged.

## 6. Testes

- **Decision**: `pytest` com cobertura mínima 90% (regra global). Testes
  unitários mockam o `git_adapter` (via `unittest.mock` ou fakes simples) ao
  testar `application`/`domain`. Um teste de integração cria repositórios
  git reais (`upstream` + `origin`/fork) em `tmp_path` para validar o
  adapter fim a fim (fetch, ff-only merge, push local, stash).
- **Rationale**: Alinhado à regra global de qualidade (`pytest`, cobertura
  90%) e ao princípio de testabilidade por camada da arquitetura escolhida.
- **Alternatives considered**: Testar apenas via mocks (sem integração real
  de git) — mais rápido, mas não validaria os comandos git reais
  (flags corretas, parsing de saída) — reforça a necessidade do teste de
  integração complementar.

## Resumo

Todas as questões técnicas relevantes para o design (Phase 1) estão
resolvidas. Nenhum item pendente de pesquisa adicional.
