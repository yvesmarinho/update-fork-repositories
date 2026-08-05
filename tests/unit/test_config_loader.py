"""
NOME: test_config_loader
TITULO: Testes do carregador/validador de configuração JSON
DATA: 05/08/2026
MODIFICADO: 05/08/2026 12:04
VERSÃO: 0.1.0
DEPEND: pytest

Histórico de modificações:
- 05/08/2026: criação inicial (T009)

STATUS: DEV
"""

from pathlib import Path

import pytest

from update_fork_repositories.domain.exceptions import ConfiguracaoInvalidaError
from update_fork_repositories.domain.models import OnDirtyWorkingTree
from update_fork_repositories.infrastructure.config_loader import carregar_config


def test_carregar_config_valido(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        '{"repositorios": [{"path": "/tmp/fork-a"}, '
        '{"path": "/tmp/fork-b", "on_dirty_working_tree": "stash"}]}',
        encoding="utf-8",
    )

    repositorios = carregar_config(config_file)

    assert len(repositorios) == 2
    assert repositorios[0].path == "/tmp/fork-a"
    assert repositorios[0].on_dirty_working_tree == OnDirtyWorkingTree.ABORT
    assert repositorios[1].on_dirty_working_tree == OnDirtyWorkingTree.STASH


def test_carregar_config_arquivo_ausente(tmp_path: Path) -> None:
    config_file = tmp_path / "nao-existe.json"

    with pytest.raises(ConfiguracaoInvalidaError):
        carregar_config(config_file)


def test_carregar_config_json_malformado(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text("{ isso nao e json", encoding="utf-8")

    with pytest.raises(ConfiguracaoInvalidaError):
        carregar_config(config_file)


def test_carregar_config_repositorios_nao_e_lista(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text('{"repositorios": "nao-e-uma-lista"}', encoding="utf-8")

    with pytest.raises(ConfiguracaoInvalidaError):
        carregar_config(config_file)


def test_carregar_config_sem_campo_repositorios(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text('{"algo_errado": []}', encoding="utf-8")

    with pytest.raises(ConfiguracaoInvalidaError):
        carregar_config(config_file)


def test_carregar_config_item_sem_path(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        '{"repositorios": [{"on_dirty_working_tree": "abort"}]}', encoding="utf-8"
    )

    with pytest.raises(ConfiguracaoInvalidaError):
        carregar_config(config_file)


def test_carregar_config_on_dirty_working_tree_invalido(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        '{"repositorios": [{"path": "/tmp/fork-a", "on_dirty_working_tree": "delete"}]}',
        encoding="utf-8",
    )

    with pytest.raises(ConfiguracaoInvalidaError):
        carregar_config(config_file)
