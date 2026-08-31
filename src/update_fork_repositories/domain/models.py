"""
NOME: models
TITULO: Modelos de domínio para sincronização de forks
DATA: 05/08/2026
MODIFICADO: 05/08/2026 15:43
VERSÃO: 0.1.0
DEPEND: nenhuma

Histórico de modificações:
- 05/08/2026: criação inicial (T005)
- 05/08/2026: status IGNORADO para pastas sem .git (alteração 02)

STATUS: DEV
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class OnDirtyWorkingTree(StrEnum):
    """Política de tratamento de mudanças locais não commitadas."""

    ABORT = "abort"
    STASH = "stash"


class StatusSincronizacao(StrEnum):
    """Resultado do processamento de um repositório em uma execução."""

    OK = "OK"
    NO_CHANGES = "NO_CHANGES"
    DIRTY = "DIRTY"
    DIVERGED = "DIVERGED"
    ERROR = "ERROR"
    IGNORADO = "IGNORADO"


@dataclass(frozen=True)
class RepositorioConfig:
    """
    Representa uma entrada do JSON de configuração.

    :param path: Caminho absoluto do repositório git local (fork).
    :type path: str
    :param on_dirty_working_tree: Política ao encontrar mudanças não commitadas.
    :type on_dirty_working_tree: OnDirtyWorkingTree
    """

    path: str
    on_dirty_working_tree: OnDirtyWorkingTree = OnDirtyWorkingTree.ABORT


@dataclass(frozen=True)
class ResultadoSincronizacao:
    """
    Representa o desfecho do processamento de um repositório em uma execução.

    :param path: Caminho do repositório processado.
    :type path: str
    :param status: Resultado do processamento.
    :type status: StatusSincronizacao
    :param mensagem: Detalhe legível do resultado.
    :type mensagem: str
    :param timestamp: Momento em que o processamento terminou.
    :type timestamp: datetime
    """

    path: str
    status: StatusSincronizacao
    mensagem: str
    timestamp: datetime
