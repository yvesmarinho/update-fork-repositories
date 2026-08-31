"""
NOME: exceptions
TITULO: Exceções de domínio para sincronização de forks
DATA: 05/08/2026
MODIFICADO: 05/08/2026 15:58
VERSÃO: 0.1.0
DEPEND: nenhuma

Histórico de modificações:
- 05/08/2026: criação inicial (T006)
- 05/08/2026: removida UpstreamAusenteError — ausência de 'upstream' deixou
  de ser erro; repositório é sincronizado a partir de 'origin' (sem push)

STATUS: DEV
"""


class RepositorioInvalidoError(Exception):
    """Levantada quando o ``path`` configurado não existe ou não é um repositório git válido."""


class ComandoGitFalhouError(Exception):
    """Levantada quando um comando ``git`` externo retorna código de saída de erro."""


class ConfiguracaoInvalidaError(Exception):
    """Levantada quando o arquivo de configuração JSON está ausente, malformado ou inválido."""
