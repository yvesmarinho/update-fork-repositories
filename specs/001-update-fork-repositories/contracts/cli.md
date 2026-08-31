# Contrato: Interface de Linha de Comando

Este projeto expõe uma única interface externa: o comando de linha de
comando instalado em `~/.local/bin/`. Não há API HTTP nem biblioteca pública
consumida por outros processos nesta fase.

## Comando

```text
update-fork-repositories [CONFIG_PATH]
```

- `CONFIG_PATH` (opcional, argumento posicional): caminho para o JSON de
  configuração. Se omitido, usa
  `~/.config/update-fork-repositories/config.json`.

## Entrada — Formato do JSON de configuração

```json
{
  "repositorios": [
    {
      "path": "/home/usuario/forks/algum-projeto",
      "on_dirty_working_tree": "abort"
    },
    {
      "path": "/home/usuario/forks/outro-projeto"
    }
  ]
}
```

- `repositorios` (obrigatório): lista de objetos.
- `path` (obrigatório por item): caminho absoluto do repositório.
- `on_dirty_working_tree` (opcional por item): `"abort"` (default) ou
  `"stash"`. Ver [data-model.md](../data-model.md).

Ver schema formal em [`config.schema.json`](./config.schema.json).

## Saída — Log (arquivo, via `logging`)

Grava em `/var/log/enterprise/update-fork-repositories.log`. Uma linha
estruturada por repositório processado, no formato padrão do `logging` do
projeto (nível, função/linha, mensagem), sempre identificando o repositório
em análise, contendo no mínimo: caminho do repositório e status (`OK` |
`NO_CHANGES` | `DIRTY` | `DIVERGED` | `ERROR` | `IGNORADO`). Erros de
configuração (JSON ausente/inválido) são logados em nível `ERROR` antes de
qualquer processamento de repositório, sem produzir resultados por item.

## Saída — Exit code

| Exit code | Condição |
|-----------|----------|
| `0`       | Configuração válida e todos os repositórios com status `OK`, `NO_CHANGES` ou `IGNORADO`. |
| `1`       | Configuração ausente/inválida (fail fast, nenhum repositório processado) OU pelo menos um repositório com status `DIRTY`, `DIVERGED` ou `ERROR`. |

## Pré-condições assumidas (não validadas pelo comando)

- Cada `path`, se existir e for um repositório git, tem ao menos o remote
  `origin` configurado. O remote `upstream` é opcional: se ausente, o
  repositório é tratado como uma cópia baixada (não um fork real) —
  sincronizado a partir de `origin`, somente localmente, sem push.
- Autenticação SSH já configurada no ambiente para `fetch`/`push`.
- Binário `git` disponível no `PATH`.

## Agendamento (cron/systemd)

O comando não gerencia seu próprio agendamento (User Story 3). Um exemplo de
unit `systemd` (`update-fork-repositories.service` + `.timer`) para execução
diária deve ser adicionado em `contracts/systemd/` nesta pasta, referenciado
a partir do `README.md` do projeto.

## Compatibilidade

Primeira versão do contrato — sem histórico de breaking changes a
documentar. Mudanças futuras no formato do JSON ou nos códigos de saída
devem ser versionadas e documentadas aqui antes da implementação.
