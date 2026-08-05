# Update Fork Repositories

[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)
[![GitHub Flow](https://img.shields.io/badge/Workflow-GitHub%20Flow-blue.svg)](https://docs.github.com/en/get-started/quickstart/github-flow)
![Branch Protection](https://img.shields.io/badge/Branch%20Protection-Recommended-green)

> Código daemon para atualizar diáriamente meus repositórios Github que são forks

**Domínio**: programming | **Linguagem**: python
**Criado em**: 2026-08-05T11:49:55Z
**Repositório**: [https://github.com/yvesmarinho/update-fork-repositories.git](https://github.com/yvesmarinho/update-fork-repositories.git)

---

## 🚀 Início Rápido

```bash
# Instalar dependências
make install-deps

# Iniciar desenvolvimento
make dev
```

## 📦 Instalação

```bash
uv tool install .
```

Isso instala o executável `update-fork-repositories` em `~/.local/bin/`
(certifique-se de que essa pasta está no seu `PATH`).

## ⚙️ Configuração

Crie o arquivo de configuração em
`~/.config/update-fork-repositories/config.json`, listando os repositórios
fork locais a sincronizar (schema completo em
[specs/001-update-fork-repositories/contracts/config.schema.json](specs/001-update-fork-repositories/contracts/config.schema.json)):

```json
{
  "repositorios": [
    { "path": "/home/usuario/forks/algum-projeto" },
    { "path": "/home/usuario/forks/outro-projeto", "on_dirty_working_tree": "stash" }
  ]
}
```

Cada repositório listado precisa já ter um remote `upstream` configurado
(`git remote add upstream <url>`), feito manualmente uma vez na criação do
fork. Detalhes completos do contrato da CLI em
[specs/001-update-fork-repositories/contracts/cli.md](specs/001-update-fork-repositories/contracts/cli.md).

## 🚀 Uso

```bash
update-fork-repositories                       # usa o config default acima
update-fork-repositories /caminho/outro.json    # ou um config alternativo
```

## ⏰ Agendamento (execução diária)

O comando não gerencia seu próprio agendamento — use `cron` ou `systemd
timer`. Exemplo de unit `systemd` em
[specs/001-update-fork-repositories/contracts/systemd/](specs/001-update-fork-repositories/contracts/systemd/):

```bash
mkdir -p ~/.config/systemd/user
cp specs/001-update-fork-repositories/contracts/systemd/update-fork-repositories.{service,timer} ~/.config/systemd/user/
systemctl --user enable --now update-fork-repositories.timer
```

Alternativa via `cron` (`crontab -e`):

```cron
0 6 * * * /home/usuario/.local/bin/update-fork-repositories
```

## 📚 Documentação

- [Índice](docs/INDEX.md)
- [Tarefas](docs/TODO.md)
- [Especificação da feature](specs/001-update-fork-repositories/spec.md)

## 🤝 Contribuindo

Este projeto segue as melhores práticas de Git/GitHub para garantir qualidade e colaboração eficiente.

### Workflow Git

Consulte [CONTRIBUTING.md](CONTRIBUTING.md) para:
- Convenções de branches (`feature/NNN-descricao`, `fix/descricao`)
- Padrões de commits (Conventional Commits)
- Processo de Pull Request
- Estratégias de merge
- Proteção de branches

### Configuração de Branch Protection

Para configurar proteção de branches no GitHub, consulte [docs/BRANCH_PROTECTION_SETUP.md](docs/BRANCH_PROTECTION_SETUP.md).

## 🏗️ Estrutura

Consulte os [documentos de arquitetura](docs/) para detalhes.
