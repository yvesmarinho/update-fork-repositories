"""
NOME: cli
TITULO: Interface de linha de comando — sincronização de forks
DATA: 05/08/2026
MODIFICADO: 05/08/2026 15:44
VERSÃO: 0.1.0
DEPEND: nenhuma (stdlib)

Histórico de modificações:
- 05/08/2026: configuração de logging estruturado (T007)
- 05/08/2026: argparse, orquestração e exit code agregado (T015)
- 05/08/2026: fail-fast em ConfiguracaoInvalidaError (T016)
- 05/08/2026: default de CONFIG_PATH em ~/.config/update-fork-repositories/config.json (T024)
- 05/08/2026: log gravado em /var/log/enterprise/update-fork-repositories.log

STATUS: DEV
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from update_fork_repositories.application.sincronizar_forks import sincronizar_forks
from update_fork_repositories.domain.exceptions import ConfiguracaoInvalidaError
from update_fork_repositories.domain.models import StatusSincronizacao
from update_fork_repositories.infrastructure.config_loader import carregar_config

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "update-fork-repositories" / "config.json"
LOG_FILE = Path("/var/log/enterprise") / "update-fork-repositories.log"
STATUS_NAO_FALHA = {
    StatusSincronizacao.OK,
    StatusSincronizacao.NO_CHANGES,
    StatusSincronizacao.IGNORADO,
}


def config_logging() -> bool:
    """
    Configura o logging estruturado do processo, uma única vez.

    Grava em :data:`LOG_FILE` (``/var/log/enterprise/update-fork-repositories.log``).

    :return: True após configuração (ou se já configurado).
    :rtype: bool
    """
    if logging.getLogger().hasHandlers():
        return True
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        filename=LOG_FILE,
    )
    return True


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="update-fork-repositories",
        description="Sincroniza repositórios fork locais com seus respectivos upstreams.",
    )
    parser.add_argument(
        "config_path",
        nargs="?",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Caminho do JSON de configuração (default: {DEFAULT_CONFIG_PATH})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """
    Ponto de entrada da CLI.

    :param argv: Argumentos de linha de comando (default: ``sys.argv[1:]``).
    :type argv: list[str] | None
    :return: Código de saída do processo — 0 se nenhum repositório falhou
        (OK/NO_CHANGES/IGNORADO), 1 caso contrário.
    :rtype: int
    """
    config_logging()
    logging.info("=== Função: main ===")

    args = _parse_args(argv)

    try:
        repositorios = carregar_config(args.config_path)
    except ConfiguracaoInvalidaError as error:
        logging.error("Configuração inválida: %s", error)
        return 1

    resultados = sincronizar_forks(repositorios)

    for resultado in resultados:
        nivel = logging.INFO if resultado.status in STATUS_NAO_FALHA else logging.WARNING
        logging.log(
            nivel, "%s: %s — %s", resultado.path, resultado.status.value, resultado.mensagem
        )

    sucesso_total = all(r.status in STATUS_NAO_FALHA for r in resultados)
    return 0 if sucesso_total else 1


if __name__ == "__main__":
    sys.exit(main())
