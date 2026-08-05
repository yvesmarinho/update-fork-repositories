"""
NOME: config_loader
TITULO: Leitura e validação do JSON de configuração
DATA: 05/08/2026
MODIFICADO: 05/08/2026 11:56
VERSÃO: 0.1.0
DEPEND: nenhuma (stdlib)

Histórico de modificações:
- 05/08/2026: criação inicial (T012, T022)

STATUS: DEV
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from update_fork_repositories.domain.exceptions import ConfiguracaoInvalidaError
from update_fork_repositories.domain.models import OnDirtyWorkingTree, RepositorioConfig

VALORES_ON_DIRTY_WORKING_TREE = {item.value for item in OnDirtyWorkingTree}


def carregar_config(config_path: Path) -> list[RepositorioConfig]:
    """
    Lê e valida o arquivo JSON de configuração.

    :param config_path: Caminho do arquivo de configuração.
    :type config_path: Path
    :raises ConfiguracaoInvalidaError: se o arquivo estiver ausente, malformado
        ou com estrutura inválida.
    :return: Lista de repositórios configurados.
    :rtype: list[RepositorioConfig]

    :Example:

    >>> import json, tempfile
    >>> from pathlib import Path
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     p = Path(tmp) / "config.json"
    ...     _ = p.write_text(json.dumps({"repositorios": [{"path": "/tmp/x"}]}))
    ...     repos = carregar_config(p)
    ...     repos[0].path
    '/tmp/x'
    """
    logging.info("=== Função: carregar_config ===")
    logging.info("==> VAR: config_path TYPE: %s, CONTENT: %s", type(config_path), config_path)

    if not config_path.is_file():
        raise ConfiguracaoInvalidaError(f"Arquivo de configuração não encontrado: {config_path}")

    try:
        conteudo = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ConfiguracaoInvalidaError(
            f"Falha ao ler/parsear {config_path}: {error}"
        ) from error

    if not isinstance(conteudo, dict) or "repositorios" not in conteudo:
        raise ConfiguracaoInvalidaError(
            f"Configuração inválida em {config_path}: campo 'repositorios' ausente"
        )

    itens = conteudo["repositorios"]
    if not isinstance(itens, list):
        raise ConfiguracaoInvalidaError(
            f"Configuração inválida em {config_path}: 'repositorios' deve ser uma lista"
        )

    return [_parse_item(item, config_path) for item in itens]


def _parse_item(item: object, config_path: Path) -> RepositorioConfig:
    if not isinstance(item, dict) or not item.get("path"):
        raise ConfiguracaoInvalidaError(
            f"Configuração inválida em {config_path}: item sem campo 'path' obrigatório"
        )

    on_dirty_raw = item.get("on_dirty_working_tree", OnDirtyWorkingTree.ABORT.value)
    if on_dirty_raw not in VALORES_ON_DIRTY_WORKING_TREE:
        raise ConfiguracaoInvalidaError(
            f"Configuração inválida em {config_path}: "
            f"'on_dirty_working_tree' deve ser um de {sorted(VALORES_ON_DIRTY_WORKING_TREE)}, "
            f"recebido {on_dirty_raw!r}"
        )

    return RepositorioConfig(
        path=item["path"],
        on_dirty_working_tree=OnDirtyWorkingTree(on_dirty_raw),
    )
