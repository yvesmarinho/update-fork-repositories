# Quickstart: Validação da Sincronização de Forks

Guia para validar manualmente, fim a fim, que a funcionalidade sincroniza
forks locais com seus upstreams — sem detalhar implementação (ver
[data-model.md](./data-model.md) e [contracts/cli.md](./contracts/cli.md)).

## Pré-requisitos

- Python 3.12+ com `uv` instalado.
- `git` disponível no `PATH`.
- Repositório do projeto clonado, com as dependências de desenvolvimento
  instaladas (`uv sync`, uma vez que a implementação exista).

## Setup — preparar um cenário de teste local

Crie dois repositórios git locais simulando "upstream" e "fork", e um
terceiro representando o clone local do fork usado pela ferramenta.

```bash
# 1) Repositório "upstream" (simula o original)
mkdir -p /tmp/uf-test/upstream && cd /tmp/uf-test/upstream
git init -q -b main && echo "v1" > arquivo.txt && git add . && git commit -qm "v1"

# 2) "Fork" remoto (simula o repositório do usuário no GitHub) — clone bare do upstream
git clone -q --bare /tmp/uf-test/upstream /tmp/uf-test/fork-remoto.git

# 3) Clone local do fork, que é o que entra na configuração da ferramenta
git clone -q /tmp/uf-test/fork-remoto.git /tmp/uf-test/meu-fork
cd /tmp/uf-test/meu-fork
git remote add upstream /tmp/uf-test/upstream

# 4) Simular uma atualização no upstream que ainda não chegou ao fork
cd /tmp/uf-test/upstream
echo "v2" >> arquivo.txt && git add . && git commit -qm "v2"
```

## Configuração

```bash
mkdir -p ~/.config/update-fork-repositories
cat > /tmp/uf-test/config.json << 'EOF'
{
  "repositorios": [
    { "path": "/tmp/uf-test/meu-fork" }
  ]
}
EOF
```

## Execução

```bash
update-fork-repositories /tmp/uf-test/config.json
echo "exit code: $?"
```

## Resultado esperado

- Log mostra o repositório `/tmp/uf-test/meu-fork` com status `OK`.
- `git -C /tmp/uf-test/meu-fork log --oneline -1` mostra o commit `v2`.
- `git --git-dir=/tmp/uf-test/fork-remoto.git log --oneline -1` também
  mostra `v2` (o push para `origin` aconteceu).
- Exit code do comando é `0`.

## Cenário 2 — Sem mudanças pendentes (idempotência)

Rodar o mesmo comando novamente sem alterar o upstream:

```bash
update-fork-repositories /tmp/uf-test/config.json
echo "exit code: $?"
```

**Esperado**: status `NO_CHANGES` para o repositório; exit code `0`; nenhum
novo commit/push.

## Cenário 3 — Working tree suja (`on_dirty_working_tree`)

```bash
echo "rascunho" >> /tmp/uf-test/meu-fork/arquivo.txt
cd /tmp/uf-test/upstream && echo "v3" >> arquivo.txt && git add . && git commit -qm "v3"

update-fork-repositories /tmp/uf-test/config.json
echo "exit code: $?"
git -C /tmp/uf-test/meu-fork status --porcelain   # mudança "rascunho" ainda presente
```

**Esperado** (config default `on_dirty_working_tree: "abort"`): status
`DIRTY`; exit code `!= 0`; arquivo com a mudança "rascunho" intacto, `v3`
NÃO incorporado.

Repita alterando a configuração do repositório para
`"on_dirty_working_tree": "stash"` e rode novamente: esperado status `OK`,
`v3` incorporado, e a mudança "rascunho" restaurada ao final
(`git status --porcelain` mostra a mesma alteração pendente de antes).

## Cenário 4 — Repositório com falha (upstream ausente) não bloqueia os demais

Adicione um segundo repositório à configuração sem remote `upstream`
configurado e rode o comando: esperado que o repositório válido continue
sendo processado normalmente (`OK`/`NO_CHANGES`) enquanto o outro é
reportado como `ERROR`, e o exit code final é `!= 0`.

## Limpeza

```bash
rm -rf /tmp/uf-test
```
