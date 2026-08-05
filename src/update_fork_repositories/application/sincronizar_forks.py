"""
NOME: sincronizar_forks
TITULO: Orquestração da sincronização de repositórios fork com upstream
DATA: 05/08/2026
MODIFICADO: 05/08/2026 12:02
VERSÃO: 0.1.0
DEPEND: nenhuma (stdlib)

Histórico de modificações:
- 05/08/2026: fluxo OK/NO_CHANGES/DIVERGED/ERROR/DIRTY(abort) (T014)
- 05/08/2026: política 'stash' para working tree suja (T021)

STATUS: DEV
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from update_fork_repositories.domain.exceptions import (
    ComandoGitFalhouError,
    RepositorioInvalidoError,
    UpstreamAusenteError,
)
from update_fork_repositories.domain.models import (
    OnDirtyWorkingTree,
    RepositorioConfig,
    ResultadoSincronizacao,
    StatusSincronizacao,
)
from update_fork_repositories.infrastructure import git_adapter

_TZ = ZoneInfo("America/Sao_Paulo")


def sincronizar_forks(repositorios: list[RepositorioConfig]) -> list[ResultadoSincronizacao]:
    """
    Processa cada repositório configurado, sincronizando-o com o upstream.

    Falha em um repositório não interrompe o processamento dos demais.

    :param repositorios: Lista de repositórios configurados.
    :type repositorios: list[RepositorioConfig]
    :return: Um resultado por repositório, na mesma ordem da entrada.
    :rtype: list[ResultadoSincronizacao]
    """
    logging.info("=== Função: sincronizar_forks ===")
    logging.info("==> VAR: total_repositorios TYPE: %s, CONTENT: %s", int, len(repositorios))

    return [_sincronizar_um(config) for config in repositorios]


def _agora() -> datetime:
    return datetime.now(_TZ)


def _sincronizar_um(config: RepositorioConfig) -> ResultadoSincronizacao:
    path = Path(config.path)
    try:
        git_adapter.validar_repositorio(path)

        if git_adapter.working_tree_sujo(path):
            return _tratar_working_tree_sujo(config, path)

        return _fetch_e_merge(path)

    except (RepositorioInvalidoError, UpstreamAusenteError, ComandoGitFalhouError) as error:
        logging.error("Falha ao sincronizar %s: %s", path, error)
        return ResultadoSincronizacao(
            path=str(path),
            status=StatusSincronizacao.ERROR,
            mensagem=str(error),
            timestamp=_agora(),
        )


def _tratar_working_tree_sujo(config: RepositorioConfig, path: Path) -> ResultadoSincronizacao:
    if config.on_dirty_working_tree == OnDirtyWorkingTree.ABORT:
        logging.info(
            "Repositório %s com mudanças não commitadas — abortando (política 'abort')", path
        )
        return ResultadoSincronizacao(
            path=str(path),
            status=StatusSincronizacao.DIRTY,
            mensagem=(
                "Working tree com mudanças não commitadas; "
                "nenhuma ação executada (política 'abort')"
            ),
            timestamp=_agora(),
        )

    git_adapter.stash_push(path)
    try:
        resultado = _fetch_e_merge(path)
    finally:
        pop_ok = git_adapter.stash_pop(path)

    if not pop_ok:
        logging.error("Falha ao restaurar stash em %s; stash preservado", path)
        return ResultadoSincronizacao(
            path=str(path),
            status=StatusSincronizacao.ERROR,
            mensagem=(
                "Falha ao restaurar (stash pop) mudanças locais após sincronizar; "
                "stash preservado"
            ),
            timestamp=_agora(),
        )
    return resultado


def _fetch_e_merge(path: Path) -> ResultadoSincronizacao:
    branch = git_adapter.branch_atual(path)
    git_adapter.fetch_upstream(path)

    if git_adapter.esta_divergente(path, branch):
        return ResultadoSincronizacao(
            path=str(path),
            status=StatusSincronizacao.DIVERGED,
            mensagem=(
                f"Histórico local diverge do upstream na branch '{branch}'; "
                "fast-forward não é possível"
            ),
            timestamp=_agora(),
        )

    if not git_adapter.upstream_tem_novidades(path, branch):
        return ResultadoSincronizacao(
            path=str(path),
            status=StatusSincronizacao.NO_CHANGES,
            mensagem=f"Já sincronizado com o upstream na branch '{branch}'",
            timestamp=_agora(),
        )

    git_adapter.fast_forward_merge(path, branch)
    git_adapter.push_origin(path, branch)
    return ResultadoSincronizacao(
        path=str(path),
        status=StatusSincronizacao.OK,
        mensagem=f"Branch '{branch}' atualizada por fast-forward e enviada para origin",
        timestamp=_agora(),
    )
