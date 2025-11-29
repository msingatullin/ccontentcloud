"""
MCP Integrations
Модуль интеграций с внешними сервисами
"""

from .base import BaseMCPIntegration, MCPResponse, MCPError, MCPStatus
from .openai import OpenAIMCP
from .vertex_ai import VertexAIIntegration
from .telegram import TelegramMCP
from .huggingface import HuggingFaceMCP
from .news import NewsMCP
from .wikipedia import WikipediaMCP
from .google_trends import GoogleTrendsMCP
from .analytics import AnalyticsMCP
from .twitter import TwitterMCP

__all__ = [
    'BaseMCPIntegration',
    'MCPResponse',
    'MCPError',
    'MCPStatus',
    'OpenAIMCP',
    'VertexAIIntegration',
    'TelegramMCP',
    'HuggingFaceMCP',
    'NewsMCP',
    'WikipediaMCP',
    'GoogleTrendsMCP',
    'AnalyticsMCP',
    'TwitterMCP',
]


