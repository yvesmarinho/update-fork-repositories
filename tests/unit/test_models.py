"""
NOME: test_models
TITULO: Testes dos modelos de domínio
DATA: 05/08/2026
MODIFICADO: 05/08/2026 15:45
VERSÃO: 0.1.0
DEPEND: pytest

Histórico de modificações:
- 05/08/2026: criação inicial (T008)

STATUS: DEV
"""

from datetime import datetime

from update_fork_repositories.domain.models import (
    OnDirtyWorkingTree,
    RepositorioConfig,
    ResultadoSincronizacao,
    StatusSincronizacao,
)


def test_repositorio_config_default_on_dirty_working_tree() -> None:
    config = RepositorioConfig(path="/tmp/algum-fork")

    assert config.path == "/tmp/algum-fork"
    assert config.on_dirty_working_tree == OnDirtyWorkingTree.ABORT


def test_repositorio_config_aceita_stash() -> None:
    config = RepositorioConfig(
        path="/tmp/algum-fork", on_dirty_working_tree=OnDirtyWorkingTree.STASH
    )

    assert config.on_dirty_working_tree == OnDirtyWorkingTree.STASH


def test_resultado_sincronizacao_campos() -> None:
    agora = datetime.now()

    resultado = ResultadoSincronizacao(
        path="/tmp/algum-fork",
        status=StatusSincronizacao.OK,
        mensagem="sincronizado com sucesso",
        timestamp=agora,
    )

    assert resultado.path == "/tmp/algum-fork"
    assert resultado.status == StatusSincronizacao.OK
    assert resultado.mensagem == "sincronizado com sucesso"
    assert resultado.timestamp == agora


def test_status_sincronizacao_valores_esperados() -> None:
    valores = {s.value for s in StatusSincronizacao}

    assert valores == {"OK", "NO_CHANGES", "DIRTY", "DIVERGED", "ERROR", "IGNORADO"}
