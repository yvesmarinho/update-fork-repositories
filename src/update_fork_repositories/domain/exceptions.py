"""
NOME: exceptions
TITULO: Exceções de domínio para sincronização de forks
DATA: 05/08/2026
MODIFICADO: 05/08/2026 11:55
VERSÃO: 0.1.0
DEPEND: nenhuma

Histórico de modificações:
- 05/08/2026: criação inicial (T006)

STATUS: DEV
"""


class RepositorioInvalidoError(Exception):
    """Levantada quando o ``path`` configurado não existe ou não é um repositório git válido."""


class UpstreamAusenteError(Exception):
    """Levantada quando o repositório não possui um remote ``upstream`` configurado."""


class ComandoGitFalhouError(Exception):
    """Levantada quando um comando ``git`` externo retorna código de saída de erro."""


class ConfiguracaoInvalidaError(Exception):
    """Levantada quando o arquivo de configuração JSON está ausente, malformado ou inválido."""
