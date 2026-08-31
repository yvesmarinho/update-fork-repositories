"""
NOME: test_git_adapter_validacao
TITULO: Testes de validação do git_adapter (path inválido) e remote_existe
DATA: 05/08/2026
MODIFICADO: 05/08/2026 15:58
VERSÃO: 0.1.0
DEPEND: pytest

Histórico de modificações:
- 05/08/2026: criação inicial (T013a) — cobre FR-010 e edge case de path inválido
- 05/08/2026: validar_repositorio não exige mais 'upstream'; remote_existe
  passa a ser a checagem usada para decidir upstream vs. origin

STATUS: DEV
"""

import subprocess
from pathlib import Path

import pytest

from update_fork_repositories.domain.exceptions import RepositorioInvalidoError
from update_fork_repositories.infrastructure.git_adapter import remote_existe, validar_repositorio


def test_validar_repositorio_path_sem_git(tmp_path: Path) -> None:
    with pytest.raises(RepositorioInvalidoError):
        validar_repositorio(tmp_path)


def test_validar_repositorio_sem_upstream_nao_levanta(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)

    validar_repositorio(tmp_path)


def test_validar_repositorio_com_upstream_nao_levanta(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "remote", "add", "upstream", "https://example.invalid/repo.git"],
        cwd=tmp_path,
        check=True,
    )

    validar_repositorio(tmp_path)


def test_remote_existe_true_quando_configurado(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "remote", "add", "upstream", "https://example.invalid/repo.git"],
        cwd=tmp_path,
        check=True,
    )

    assert remote_existe(tmp_path, "upstream") is True


def test_remote_existe_false_quando_ausente(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)

    assert remote_existe(tmp_path, "upstream") is False
