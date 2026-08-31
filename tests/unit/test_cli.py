"""
NOME: test_cli
TITULO: Testes da CLI — exit code agregado e resolução do config default
DATA: 05/08/2026
MODIFICADO: 05/08/2026 15:44
VERSÃO: 0.1.0
DEPEND: pytest

Histórico de modificações:
- 05/08/2026: exit code 0 (todos OK/NO_CHANGES) vs != 0 (T023)
- 05/08/2026: fail-fast em config inválida (T016)
- 05/08/2026: default de CONFIG_PATH via Path.home() (T024)

STATUS: DEV
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from update_fork_repositories.cli import DEFAULT_CONFIG_PATH, main
from update_fork_repositories.domain.models import (
    RepositorioConfig,
    ResultadoSincronizacao,
    StatusSincronizacao,
)


def _resultado(status: StatusSincronizacao) -> ResultadoSincronizacao:
    return ResultadoSincronizacao(
        path="/tmp/fork", status=status, mensagem="", timestamp=datetime.now()
    )


@patch("update_fork_repositories.cli.sincronizar_forks")
@patch("update_fork_repositories.cli.carregar_config")
def test_exit_code_zero_quando_tudo_ok(mock_carregar: object, mock_sincronizar: object) -> None:
    mock_carregar.return_value = [RepositorioConfig(path="/tmp/fork")]
    mock_sincronizar.return_value = [_resultado(StatusSincronizacao.OK)]

    assert main(["/tmp/config.json"]) == 0


@patch("update_fork_repositories.cli.sincronizar_forks")
@patch("update_fork_repositories.cli.carregar_config")
def test_exit_code_zero_com_no_changes(mock_carregar: object, mock_sincronizar: object) -> None:
    mock_carregar.return_value = [RepositorioConfig(path="/tmp/fork")]
    mock_sincronizar.return_value = [_resultado(StatusSincronizacao.NO_CHANGES)]

    assert main(["/tmp/config.json"]) == 0


@patch("update_fork_repositories.cli.sincronizar_forks")
@patch("update_fork_repositories.cli.carregar_config")
def test_exit_code_zero_com_pasta_ignorada(
    mock_carregar: object, mock_sincronizar: object
) -> None:
    mock_carregar.return_value = [
        RepositorioConfig(path="/tmp/fork-ok"),
        RepositorioConfig(path="/tmp/nao-e-git"),
    ]
    mock_sincronizar.return_value = [
        _resultado(StatusSincronizacao.OK),
        _resultado(StatusSincronizacao.IGNORADO),
    ]

    assert main(["/tmp/config.json"]) == 0


@patch("update_fork_repositories.cli.sincronizar_forks")
@patch("update_fork_repositories.cli.carregar_config")
def test_exit_code_diferente_de_zero_com_falha_isolada(
    mock_carregar: object, mock_sincronizar: object
) -> None:
    mock_carregar.return_value = [
        RepositorioConfig(path="/tmp/fork-ok"),
        RepositorioConfig(path="/tmp/fork-erro"),
    ]
    mock_sincronizar.return_value = [
        _resultado(StatusSincronizacao.OK),
        _resultado(StatusSincronizacao.ERROR),
    ]

    assert main(["/tmp/config.json"]) != 0


@patch("update_fork_repositories.cli.carregar_config")
def test_exit_code_diferente_de_zero_com_config_invalida(mock_carregar: object) -> None:
    from update_fork_repositories.domain.exceptions import ConfiguracaoInvalidaError

    mock_carregar.side_effect = ConfiguracaoInvalidaError("json malformado")

    assert main(["/tmp/config.json"]) != 0


def test_default_config_path_e_em_config_home() -> None:
    esperado = Path.home() / ".config" / "update-fork-repositories" / "config.json"
    assert DEFAULT_CONFIG_PATH == esperado
