"""
NOME: test_sincronizar_forks
TITULO: Testes da orquestração de sincronização (application), com git_adapter mockado
DATA: 05/08/2026
MODIFICADO: 05/08/2026 12:03
VERSÃO: 0.1.0
DEPEND: pytest

Histórico de modificações:
- 05/08/2026: casos OK, NO_CHANGES, ERROR isolado não bloqueia os demais (T010)
- 05/08/2026: caso DIRTY com política 'abort' (T017)

STATUS: DEV
"""

from pathlib import Path
from unittest.mock import patch

from update_fork_repositories.application.sincronizar_forks import sincronizar_forks
from update_fork_repositories.domain.exceptions import (
    ComandoGitFalhouError,
    RepositorioInvalidoError,
    UpstreamAusenteError,
)
from update_fork_repositories.domain.models import (
    OnDirtyWorkingTree,
    RepositorioConfig,
    StatusSincronizacao,
)


def _config(
    path: str, on_dirty: OnDirtyWorkingTree = OnDirtyWorkingTree.ABORT
) -> RepositorioConfig:
    return RepositorioConfig(path=path, on_dirty_working_tree=on_dirty)


@patch("update_fork_repositories.application.sincronizar_forks.git_adapter")
def test_repositorio_atualizado_com_sucesso(mock_adapter: object) -> None:
    mock_adapter.validar_repositorio.return_value = None
    mock_adapter.working_tree_sujo.return_value = False
    mock_adapter.branch_atual.return_value = "main"
    mock_adapter.fetch_upstream.return_value = None
    mock_adapter.esta_divergente.return_value = False
    mock_adapter.upstream_tem_novidades.return_value = True
    mock_adapter.fast_forward_merge.return_value = None
    mock_adapter.push_origin.return_value = None

    resultados = sincronizar_forks([_config("/tmp/fork-a")])

    assert len(resultados) == 1
    assert resultados[0].status == StatusSincronizacao.OK
    mock_adapter.push_origin.assert_called_once_with(Path("/tmp/fork-a"), "main")


@patch("update_fork_repositories.application.sincronizar_forks.git_adapter")
def test_repositorio_ja_sincronizado_sem_mudancas(mock_adapter: object) -> None:
    mock_adapter.validar_repositorio.return_value = None
    mock_adapter.working_tree_sujo.return_value = False
    mock_adapter.branch_atual.return_value = "main"
    mock_adapter.fetch_upstream.return_value = None
    mock_adapter.esta_divergente.return_value = False
    mock_adapter.upstream_tem_novidades.return_value = False

    resultados = sincronizar_forks([_config("/tmp/fork-a")])

    assert resultados[0].status == StatusSincronizacao.NO_CHANGES
    mock_adapter.push_origin.assert_not_called()


@patch("update_fork_repositories.application.sincronizar_forks.git_adapter")
def test_repositorio_divergente_nao_faz_merge(mock_adapter: object) -> None:
    mock_adapter.validar_repositorio.return_value = None
    mock_adapter.working_tree_sujo.return_value = False
    mock_adapter.branch_atual.return_value = "main"
    mock_adapter.fetch_upstream.return_value = None
    mock_adapter.esta_divergente.return_value = True

    resultados = sincronizar_forks([_config("/tmp/fork-a")])

    assert resultados[0].status == StatusSincronizacao.DIVERGED
    mock_adapter.fast_forward_merge.assert_not_called()


@patch("update_fork_repositories.application.sincronizar_forks.git_adapter")
def test_falha_em_um_repositorio_nao_bloqueia_os_demais(mock_adapter: object) -> None:
    def validar_repositorio(path: Path) -> None:
        if str(path) == "/tmp/fork-com-erro":
            raise UpstreamAusenteError("sem upstream")

    mock_adapter.validar_repositorio.side_effect = validar_repositorio
    mock_adapter.working_tree_sujo.return_value = False
    mock_adapter.branch_atual.return_value = "main"
    mock_adapter.fetch_upstream.return_value = None
    mock_adapter.esta_divergente.return_value = False
    mock_adapter.upstream_tem_novidades.return_value = False

    resultados = sincronizar_forks(
        [_config("/tmp/fork-com-erro"), _config("/tmp/fork-ok")]
    )

    assert resultados[0].status == StatusSincronizacao.ERROR
    assert resultados[1].status == StatusSincronizacao.NO_CHANGES


@patch("update_fork_repositories.application.sincronizar_forks.git_adapter")
def test_repositorio_invalido_reportado_como_erro(mock_adapter: object) -> None:
    mock_adapter.validar_repositorio.side_effect = RepositorioInvalidoError("path inválido")

    resultados = sincronizar_forks([_config("/tmp/nao-existe")])

    assert resultados[0].status == StatusSincronizacao.ERROR


@patch("update_fork_repositories.application.sincronizar_forks.git_adapter")
def test_falha_de_comando_git_reportada_como_erro(mock_adapter: object) -> None:
    mock_adapter.validar_repositorio.return_value = None
    mock_adapter.working_tree_sujo.return_value = False
    mock_adapter.branch_atual.return_value = "main"
    mock_adapter.fetch_upstream.side_effect = ComandoGitFalhouError("falha de rede")

    resultados = sincronizar_forks([_config("/tmp/fork-a")])

    assert resultados[0].status == StatusSincronizacao.ERROR


@patch("update_fork_repositories.application.sincronizar_forks.git_adapter")
def test_working_tree_sujo_com_politica_abort(mock_adapter: object) -> None:
    mock_adapter.validar_repositorio.return_value = None
    mock_adapter.working_tree_sujo.return_value = True

    resultados = sincronizar_forks([_config("/tmp/fork-a", OnDirtyWorkingTree.ABORT)])

    assert resultados[0].status == StatusSincronizacao.DIRTY
    mock_adapter.fetch_upstream.assert_not_called()


@patch("update_fork_repositories.application.sincronizar_forks.git_adapter")
def test_working_tree_sujo_com_politica_stash_sincroniza_e_restaura(mock_adapter: object) -> None:
    mock_adapter.validar_repositorio.return_value = None
    mock_adapter.working_tree_sujo.return_value = True
    mock_adapter.branch_atual.return_value = "main"
    mock_adapter.fetch_upstream.return_value = None
    mock_adapter.esta_divergente.return_value = False
    mock_adapter.upstream_tem_novidades.return_value = True
    mock_adapter.fast_forward_merge.return_value = None
    mock_adapter.push_origin.return_value = None
    mock_adapter.stash_pop.return_value = True

    resultados = sincronizar_forks([_config("/tmp/fork-a", OnDirtyWorkingTree.STASH)])

    assert resultados[0].status == StatusSincronizacao.OK
    mock_adapter.stash_push.assert_called_once_with(Path("/tmp/fork-a"))
    mock_adapter.stash_pop.assert_called_once_with(Path("/tmp/fork-a"))


@patch("update_fork_repositories.application.sincronizar_forks.git_adapter")
def test_working_tree_sujo_com_stash_pop_falho_reporta_erro_preservando_stash(
    mock_adapter: object,
) -> None:
    mock_adapter.validar_repositorio.return_value = None
    mock_adapter.working_tree_sujo.return_value = True
    mock_adapter.branch_atual.return_value = "main"
    mock_adapter.fetch_upstream.return_value = None
    mock_adapter.esta_divergente.return_value = False
    mock_adapter.upstream_tem_novidades.return_value = False
    mock_adapter.stash_pop.return_value = False

    resultados = sincronizar_forks([_config("/tmp/fork-a", OnDirtyWorkingTree.STASH)])

    assert resultados[0].status == StatusSincronizacao.ERROR
    assert "stash" in resultados[0].mensagem.lower()
