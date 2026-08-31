"""
NOME: git_adapter
TITULO: Adapter de operações git via subprocess
DATA: 05/08/2026
MODIFICADO: 05/08/2026 15:57
VERSÃO: 0.1.0
DEPEND: git (binário externo, via subprocess)

Histórico de modificações:
- 05/08/2026: criação inicial — validação, fetch, fast-forward, push (T013)
- 05/08/2026: validação de path/.git e de remote upstream ausente (T013 — G1/G2)
- 05/08/2026: working tree suja e stash (T019, T020)
- 05/08/2026: remote de sincronização parametrizável (upstream OU origin) —
  repositórios baixados/clonados sem fork real usam 'origin' como fonte,
  sem que validar_repositorio exija 'upstream' configurado

STATUS: DEV
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from update_fork_repositories.domain.exceptions import (
    ComandoGitFalhouError,
    RepositorioInvalidoError,
)

UPSTREAM_REMOTE_NAME = "upstream"
ORIGIN_REMOTE_NAME = "origin"


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Executa um comando git e retorna o resultado, sem levantar em caso de erro."""
    logging.info(
        "==> REPO: %s, VAR: git_args TYPE: %s, CONTENT: %s", cwd, type(args), ["git", *args]
    )
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
    Valida que ``path`` é um repositório git válido.

    :param path: Caminho do repositório local.
    :type path: Path
    :raises RepositorioInvalidoError: se ``path`` não existir ou não for um repositório git.
    """
    logging.info("=== Função: validar_repositorio === REPO: %s", path)

    if not (path / ".git").exists():
        raise RepositorioInvalidoError(f"{path} não existe ou não é um repositório git válido")


def remote_existe(path: Path, remote_name: str) -> bool:
    """Retorna True se o remote ``remote_name`` estiver configurado no repositório."""
    resultado = _run_git(["remote", "get-url", remote_name], path)
    return resultado.returncode == 0


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


def fetch_remote(path: Path, remote_name: str) -> None:
    """Busca as atualizações do remote informado (``upstream`` ou ``origin``)."""
    _run_git_ok(["fetch", remote_name], path, f"executar git fetch {remote_name}")


def esta_divergente(path: Path, branch: str, remote_name: str) -> bool:
    """
    Verifica se o histórico local diverge do remote (fast-forward não é possível).

    :return: True se houver commits locais que não estão no remote (divergência).
    :rtype: bool
    """
    resultado = _run_git_ok(
        ["rev-list", "--left-right", "--count", f"{branch}...{remote_name}/{branch}"],
        path,
        f"comparar branch local com {remote_name}",
    )
    a_frente_local, _atras_local = resultado.stdout.strip().split()
    return int(a_frente_local) > 0


def remote_tem_novidades(path: Path, branch: str, remote_name: str) -> bool:
    """Verifica se o remote tem commits que a branch local ainda não possui."""
    resultado = _run_git_ok(
        ["rev-list", "--left-right", "--count", f"{branch}...{remote_name}/{branch}"],
        path,
        f"comparar branch local com {remote_name}",
    )
    _a_frente_local, atras_local = resultado.stdout.strip().split()
    return int(atras_local) > 0


def fast_forward_merge(path: Path, branch: str, remote_name: str) -> None:
    """Aplica fast-forward merge das mudanças do remote informado na branch local."""
    _run_git_ok(
        ["merge", "--ff-only", f"{remote_name}/{branch}"],
        path,
        "executar git merge --ff-only",
    )


def push_origin(path: Path, branch: str) -> None:
    """Envia a branch local atualizada para o remote ``origin``."""
    _run_git_ok(["push", ORIGIN_REMOTE_NAME, branch], path, "executar git push origin")
