"""
NOME: test_git_adapter
TITULO: Testes de integração do git_adapter com repositórios git reais
DATA: 05/08/2026
MODIFICADO: 05/08/2026 12:04
VERSÃO: 0.1.0
DEPEND: pytest, git (binário externo)

Histórico de modificações:
- 05/08/2026: fetch, fast-forward, push, divergência (T011)
- 05/08/2026: stash push/pop, com e sem falha no pop (T018)

STATUS: DEV
"""

import subprocess
from pathlib import Path

import pytest

from update_fork_repositories.domain.exceptions import ComandoGitFalhouError
from update_fork_repositories.infrastructure.git_adapter import (
    branch_atual,
    esta_divergente,
    fast_forward_merge,
    fetch_remote,
    push_origin,
    remote_tem_novidades,
    stash_pop,
    stash_push,
    working_tree_sujo,
)


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def cenario_fork(tmp_path: Path) -> Path:
    """
    Cria upstream + fork remoto (bare) + clone local do fork, com remote
    'upstream' configurado, replicando o pré-requisito documentado em
    quickstart.md.
    """
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _git(["init", "-q", "-b", "main"], upstream)
    (upstream / "arquivo.txt").write_text("v1\n", encoding="utf-8")
    _git(["add", "."], upstream)
    _git(["-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-qm", "v1"], upstream)

    fork_remoto = tmp_path / "fork-remoto.git"
    _git(["clone", "-q", "--bare", str(upstream), str(fork_remoto)], tmp_path)

    meu_fork = tmp_path / "meu-fork"
    _git(["clone", "-q", str(fork_remoto), str(meu_fork)], tmp_path)
    _git(["remote", "add", "upstream", str(upstream)], meu_fork)
    _git(["config", "user.email", "t@t.com"], meu_fork)
    _git(["config", "user.name", "t"], meu_fork)

    return meu_fork


def test_branch_atual_retorna_o_head_do_repositorio(cenario_fork: Path) -> None:
    assert branch_atual(cenario_fork) == "main"


def test_fetch_upstream_falha_levanta_comando_git_falhou(cenario_fork: Path) -> None:
    _git(["remote", "remove", "upstream"], cenario_fork)
    _git(["remote", "add", "upstream", "/caminho/que/nao/existe"], cenario_fork)

    with pytest.raises(ComandoGitFalhouError):
        fetch_remote(cenario_fork, "upstream")


def test_fetch_e_fast_forward_traz_novidades_do_upstream(cenario_fork: Path) -> None:
    upstream = cenario_fork.parent / "upstream"
    (upstream / "arquivo.txt").write_text("v1\nv2\n", encoding="utf-8")
    _git(["add", "."], upstream)
    _git(["-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-qm", "v2"], upstream)

    fetch_remote(cenario_fork, "upstream")

    assert remote_tem_novidades(cenario_fork, "main", "upstream") is True
    assert esta_divergente(cenario_fork, "main", "upstream") is False

    fast_forward_merge(cenario_fork, "main", "upstream")

    conteudo = (cenario_fork / "arquivo.txt").read_text(encoding="utf-8")
    assert conteudo == "v1\nv2\n"


def test_push_origin_envia_atualizacao_para_o_fork_remoto(cenario_fork: Path) -> None:
    upstream = cenario_fork.parent / "upstream"
    (upstream / "arquivo.txt").write_text("v1\nv2\n", encoding="utf-8")
    _git(["add", "."], upstream)
    _git(["-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-qm", "v2"], upstream)

    fetch_remote(cenario_fork, "upstream")
    fast_forward_merge(cenario_fork, "main", "upstream")
    push_origin(cenario_fork, "main")

    fork_remoto = cenario_fork.parent / "fork-remoto.git"
    log_remoto = _git(["log", "--oneline", "-1"], fork_remoto).stdout
    log_local = _git(["log", "--oneline", "-1"], cenario_fork).stdout
    assert log_remoto.split()[0] == log_local.split()[0]


def test_sem_novidades_no_upstream(cenario_fork: Path) -> None:
    fetch_remote(cenario_fork, "upstream")

    assert remote_tem_novidades(cenario_fork, "main", "upstream") is False


def test_historico_divergente_nao_permite_fast_forward(cenario_fork: Path) -> None:
    (cenario_fork / "arquivo.txt").write_text("v1\nlocal\n", encoding="utf-8")
    _git(["add", "."], cenario_fork)
    _git(["commit", "-qm", "mudanca local"], cenario_fork)

    upstream = cenario_fork.parent / "upstream"
    (upstream / "arquivo.txt").write_text("v1\nupstream\n", encoding="utf-8")
    _git(["add", "."], upstream)
    _git(
        ["-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-qm", "mudanca upstream"],
        upstream,
    )

    fetch_remote(cenario_fork, "upstream")

    assert esta_divergente(cenario_fork, "main", "upstream") is True


def test_stash_push_e_pop_preserva_mudancas_locais(cenario_fork: Path) -> None:
    (cenario_fork / "arquivo.txt").write_text("v1\nrascunho\n", encoding="utf-8")

    assert working_tree_sujo(cenario_fork) is True

    stash_push(cenario_fork)
    assert working_tree_sujo(cenario_fork) is False

    assert stash_pop(cenario_fork) is True
    assert working_tree_sujo(cenario_fork) is True
    assert "rascunho" in (cenario_fork / "arquivo.txt").read_text(encoding="utf-8")


def test_stash_pop_com_conflito_preserva_o_stash(cenario_fork: Path) -> None:
    (cenario_fork / "arquivo.txt").write_text("v1\nrascunho\n", encoding="utf-8")
    stash_push(cenario_fork)

    (cenario_fork / "arquivo.txt").write_text("v1\noutra-mudanca-conflitante\n", encoding="utf-8")
    _git(["add", "."], cenario_fork)
    _git(["commit", "-qm", "mudanca que vai conflitar com o stash"], cenario_fork)

    sucesso = stash_pop(cenario_fork)

    assert sucesso is False
    lista_stash = _git(["stash", "list"], cenario_fork).stdout
    assert lista_stash.strip() != ""
