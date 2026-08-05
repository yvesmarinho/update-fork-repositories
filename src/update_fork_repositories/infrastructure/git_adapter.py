"""
NOME: git_adapter
TITULO: Adapter de operações git via subprocess
DATA: 05/08/2026
MODIFICADO: 05/08/2026 11:56
VERSÃO: 0.1.0
DEPEND: git (binário externo, via subprocess)

Histórico de modificações:
- 05/08/2026: criação inicial — validação, fetch, fast-forward, push (T013)
- 05/08/2026: validação de path/.git e de remote upstream ausente (T013 — G1/G2)
- 05/08/2026: working tree suja e stash (T019, T020)

STATUS: DEV
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from update_fork_repositories.domain.exceptions import (
    ComandoGitFalhouError,
    RepositorioInvalidoError,
    UpstreamAusenteError,
)

UPSTREAM_REMOTE_NAME = "upstream"
ORIGIN_REMOTE_NAME = "origin"


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Executa um comando git e retorna o resultado, sem levantar em caso de erro."""
    logging.info("==> VAR: git_args TYPE: %s, CONTENT: %s", type(args), ["git", *args])
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_git_ok(args: list[str], cwd: Path, acao: str) -> subprocess.CompletedProcess[str]:
    """Executa um comando git exigindo sucesso; levanta ComandoGitFalhouError caso contrário."""
    resultado = _run_git(args, cwd)
    if resultado.returncode != 0:
        raise ComandoGitFalhouError(
            f"Falha ao {acao} em {cwd}: {resultado.stderr.strip() or resultado.stdout.strip()}"
        )
    return resultado


def validar_repositorio(path: Path) -> None:
    """
    Valida que ``path`` é um repositório git com remote ``upstream`` configurado.

    :param path: Caminho do repositório local.
    :type path: Path
    :raises RepositorioInvalidoError: se ``path`` não existir ou não for um repositório git.
    :raises UpstreamAusenteError: se o remote ``upstream`` não estiver configurado.
    """
    logging.info("=== Função: validar_repositorio ===")

    if not (path / ".git").exists():
        raise RepositorioInvalidoError(f"{path} não existe ou não é um repositório git válido")

    resultado = _run_git(["remote", "get-url", UPSTREAM_REMOTE_NAME], path)
    if resultado.returncode != 0:
        raise UpstreamAusenteError(
            f"Remote '{UPSTREAM_REMOTE_NAME}' não configurado em {path}"
        )


def branch_atual(path: Path) -> str:
    """Retorna o nome da branch atual (HEAD) do repositório."""
    resultado = _run_git_ok(["rev-parse", "--abbrev-ref", "HEAD"], path, "obter branch atual")
    return resultado.stdout.strip()


def working_tree_sujo(path: Path) -> bool:
    """Retorna True se houver mudanças não commitadas no repositório."""
    resultado = _run_git_ok(["status", "--porcelain"], path, "verificar status do working tree")
    return bool(resultado.stdout.strip())


def stash_push(path: Path) -> None:
    """Guarda temporariamente as mudanças locais não commitadas."""
    _run_git_ok(["stash", "push", "--include-untracked"], path, "executar git stash push")


def stash_pop(path: Path) -> bool:
    """
    Restaura as mudanças guardadas por :func:`stash_push`.

    :return: True se a restauração teve sucesso; False se falhou (stash preservado).
    :rtype: bool
    """
    resultado = _run_git(["stash", "pop"], path)
    return resultado.returncode == 0


def fetch_upstream(path: Path) -> None:
    """Busca as atualizações do remote ``upstream``."""
    _run_git_ok(["fetch", UPSTREAM_REMOTE_NAME], path, "executar git fetch upstream")


def esta_divergente(path: Path, branch: str) -> bool:
    """
    Verifica se o histórico local diverge do upstream (fast-forward não é possível).

    :return: True se houver commits locais que não estão no upstream (divergência).
    :rtype: bool
    """
    resultado = _run_git_ok(
        ["rev-list", "--left-right", "--count", f"{branch}...{UPSTREAM_REMOTE_NAME}/{branch}"],
        path,
        "comparar branch local com upstream",
    )
    a_frente_local, _atras_local = resultado.stdout.strip().split()
    return int(a_frente_local) > 0


def upstream_tem_novidades(path: Path, branch: str) -> bool:
    """Verifica se o upstream tem commits que a branch local ainda não possui."""
    resultado = _run_git_ok(
        ["rev-list", "--left-right", "--count", f"{branch}...{UPSTREAM_REMOTE_NAME}/{branch}"],
        path,
        "comparar branch local com upstream",
    )
    _a_frente_local, atras_local = resultado.stdout.strip().split()
    return int(atras_local) > 0


def fast_forward_merge(path: Path, branch: str) -> None:
    """Aplica fast-forward merge das mudanças do upstream na branch local."""
    _run_git_ok(
        ["merge", "--ff-only", f"{UPSTREAM_REMOTE_NAME}/{branch}"],
        path,
        "executar git merge --ff-only",
    )


def push_origin(path: Path, branch: str) -> None:
    """Envia a branch local atualizada para o remote ``origin``."""
    _run_git_ok(["push", ORIGIN_REMOTE_NAME, branch], path, "executar git push origin")
