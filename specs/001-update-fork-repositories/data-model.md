# Data Model: Sincronização de Repositórios Fork com Upstream

## RepositorioConfig

Representa uma entrada do JSON de configuração — um fork local a sincronizar.

| Campo                  | Tipo   | Obrigatório | Default    | Descrição |
|-------------------------|--------|-------------|------------|-----------|
| `path`                  | string | sim         | —          | Caminho absoluto da pasta do repositório git local. |
| `on_dirty_working_tree` | string | não         | `"abort"`  | Política ao encontrar mudanças não commitadas: `"abort"` ou `"stash"`. |

**Regras de validação**:
- `path` deve ser string não vazia; validado quanto à existência e à
  presença de `.git` apenas no momento do processamento do repositório
  (não na validação inicial do JSON, para permitir reportar por item).
- `on_dirty_working_tree`, se presente, deve ser exatamente `"abort"` ou
  `"stash"` — qualquer outro valor é erro de configuração (fail fast na
  validação inicial do JSON, FR-002).

**Estrutura do arquivo de configuração** (`ConfigArquivo`):

| Campo          | Tipo                     | Obrigatório | Descrição |
|-----------------|---------------------------|-------------|-----------|
| `repositorios` | lista de `RepositorioConfig` | sim | Lista de repositórios a processar nesta execução. |

## StatusSincronizacao (enum)

| Valor        | Significado |
|--------------|-------------|
| `OK`         | Repositório estava atrasado em relação ao remote de referência e foi atualizado (fast-forward, com push apenas se houver `upstream`). |
| `NO_CHANGES` | Repositório já estava sincronizado com o remote de referência; nenhuma ação necessária. |
| `DIRTY`      | Repositório tem mudanças não commitadas e `on_dirty_working_tree == "abort"`; nada foi alterado. |
| `DIVERGED`   | Histórico local diverge do remote de referência; fast-forward não é possível; nada foi mesclado. |
| `ERROR`      | Falha de infraestrutura (falha de rede/comando git, falha ao restaurar stash, etc.). |
| `IGNORADO`   | `path` não existe ou não é um repositório git válido — pasta ignorada, sem afetar o exit code. |

**Remote de referência**: se o repositório tiver um remote `upstream`
configurado, ele é a fonte (fluxo original de fork) e o resultado é enviado
(`push`) para `origin`. Se **não** houver `upstream` — caso típico de uma
pasta apenas baixada/clonada, sem ser de fato um fork — o remote `origin` é
usado como fonte, a atualização é feita **somente na cópia local**, e
**nada é enviado** para lugar nenhum.

## ResultadoSincronizacao

Representa o desfecho do processamento de **um** `RepositorioConfig` em uma
execução.

| Campo        | Tipo                  | Descrição |
|--------------|------------------------|-----------|
| `path`       | string                 | Caminho do repositório processado (rastreabilidade no log). |
| `status`     | `StatusSincronizacao`  | Resultado do processamento. |
| `mensagem`   | string                 | Detalhe legível do resultado (ex.: commit antes/depois, motivo do erro). |
| `timestamp`  | datetime (America/Sao_Paulo) | Momento em que o processamento deste repositório terminou. |

**Relacionamento**: uma execução do comando produz uma lista de
`ResultadoSincronizacao`, um por `RepositorioConfig` da configuração, na
mesma ordem em que aparecem no JSON.

## Regra de agregação (nível de execução)

- Exit code do processo = `0` **somente se** todo `ResultadoSincronizacao`
  da execução tiver `status` em `{OK, NO_CHANGES, IGNORADO}`.
- Qualquer `DIRTY`, `DIVERGED` ou `ERROR` em pelo menos um item força exit
  code `!= 0` para a execução inteira (FR-008), sem impedir que os demais
  repositórios tenham sido processados normalmente (FR-006).

## Exceções de domínio (`domain/exceptions.py`)

Usadas internamente pelo `infrastructure`/`application` para sinalizar
condições específicas antes de serem convertidas em `ResultadoSincronizacao`
pela camada de aplicação (nunca vazam para a camada de apresentação como
exceção crua):

- `RepositorioInvalidoError` — `path` não existe ou não é um repositório git;
  resulta em status `IGNORADO`, não em `ERROR`.
- `ComandoGitFalhouError` — um comando `git` retornou código de saída de
  erro (rede, autenticação, etc.); mensagem original do git preservada.
- `ConfiguracaoInvalidaError` — JSON de configuração ausente, malformado, ou
  com `on_dirty_working_tree` com valor fora do enum aceito (fail fast,
  levantada antes de processar qualquer repositório).
