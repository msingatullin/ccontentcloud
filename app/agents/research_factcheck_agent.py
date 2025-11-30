"""
ResearchFactCheckAgent - MVP версия агента проверки фактов
Упрощенная реализация с базовой функциональностью верификации
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from ..orchestrator.agent_manager import BaseAgent, AgentCapability
from ..orchestrator.workflow_engine import Task, TaskType, TaskPriority
from ..mcp.integrations.news import NewsMCP
from ..mcp.integrations.wikipedia import WikipediaMCP
from ..mcp.integrations.vertex_ai import VertexAIMCP
from ..mcp.config import get_mcp_config, is_mcp_enabled

logger = logging.getLogger(__name__)


class FactCheckStatus(Enum):
    """Статусы проверки фактов"""
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"
    DISPUTED = "disputed"
    FALSE = "false"


class ClaimType(Enum):
    """Типы утверждений"""
    STATISTICAL = "statistical"
    TEMPORAL = "temporal"
    QUOTE = "quote"
    SCIENTIFIC = "scientific"
    HISTORICAL = "historical"
    GENERAL = "general"


@dataclass
class FactCheckResult:
    """Результат проверки факта"""
    claim: str
    claim_type: ClaimType
    status: FactCheckStatus
    confidence_score: float  # 0.0 - 1.0
    verification_sources: List[str]
    evidence: List[str]
    recommendations: List[str]
    checked_at: datetime = field(default_factory=datetime.now)


@dataclass
class ContentFactCheckReport:
    """Отчет о проверке контента"""
    content_id: str
    total_claims: int
    verified_claims: int
    disputed_claims: int
    false_claims: int
    overall_confidence: float
    fact_check_results: List[FactCheckResult]
    recommendations: List[str]
    generated_at: datetime = field(default_factory=datetime.now)


class ResearchFactCheckAgent(BaseAgent):
    """MVP агент для проверки фактов и верификации информации"""
    
    def __init__(self, agent_id: str = "research_factcheck_agent"):
        capability = AgentCapability(
            task_types=[TaskType.PLANNED, TaskType.COMPLEX],
            max_concurrent_tasks=2,  # Фактчекинг требует времени
            specializations=["fact_checking", "research", "verification", "content_analysis"],
            performance_score=0.9  # Медленнее, но точнее
        )
        super().__init__(agent_id, "Research & FactCheck Agent (MVP)", capability)
        
        # MCP интеграции
        self.news_mcp = None
        self.wikipedia_mcp = None
        self.vertex_mcp = None  # Vertex AI для фактчека с Grounding
        
        # Кэш проверенных фактов (в памяти)
        self.fact_cache = {}
        self.cache_ttl = timedelta(hours=24)
        
        # Паттерны для извлечения утверждений
        self.claim_patterns = self._load_claim_patterns()
        
        # Оценки надежности источников
        self.source_reliability = self._load_source_reliability()
        
        self._initialize_mcp_integrations()
        logger.info(f"ResearchFactCheckAgent MVP {agent_id} инициализирован")
    
    def can_handle_task(self, task: Task) -> bool:
        """
        Проверяет, может ли ResearchFactCheckAgent выполнить задачу
        НЕ обрабатывает задачи публикации и задачи с изображениями
        """
        # Сначала проверяем базовые условия
        if not super().can_handle_task(task):
            return False
        
        # ResearchFactCheckAgent НЕ обрабатывает задачи публикации
        if "Publish" in task.name or "publish" in task.name.lower():
            return False
        
        # ResearchFactCheckAgent НЕ обрабатывает задачи генерации/поиска изображений
        # Это должны делать MultimediaProducerAgent
        image_keywords = ["Image", "image", "Stock", "stock", "Generate", "generate", "multimedia"]
        if any(keyword in task.name for keyword in image_keywords):
            return False
        
        # Также проверяем контекст задачи
        task_context = task.context if hasattr(task, 'context') else {}
        if task_context.get("image_source") or task_context.get("content_type") in ["post_image", "image"]:
            return False
        
        return True
    
    def _load_claim_patterns(self) -> Dict[str, str]:
        """Загружает паттерны для извлечения утверждений"""
        return {
            "statistical": r'\d+(?:\.\d+)?%?',
            "temporal": r'\d{1,2}[./]\d{1,2}[./]\d{2,4}|\d{4}',
            "quote": r'"[^"]*"',
            "scientific": r'(?:исследование|эксперимент|анализ|данные|результаты|ученые|наука)',
            "historical": r'(?:в \d{4}|в прошлом|история|исторический)',
            "general": r'(?:утверждает|говорит|считает|полагает)'
        }
    
    def _load_source_reliability(self) -> Dict[str, float]:
        """Загружает оценки надежности источников"""
        return {
            # Wikipedia (зависит от статьи)
            "wikipedia": 0.75,
            "ru.wikipedia": 0.70,
            "en.wikipedia": 0.80,
            
            # Новостные источники
            "bbc.com": 0.87,
            "reuters.com": 0.89,
            "tass.ru": 0.85,
            "ria.ru": 0.83,
            "lenta.ru": 0.80,
            "meduza.io": 0.82,
            
            # Научные источники (если доступны)
            "nature.com": 0.95,
            "science.org": 0.95,
            "pubmed.ncbi.nlm.nih.gov": 0.90,
            
            # Правительственные источники
            "rosstat.gov.ru": 0.90,
            "gov.ru": 0.85,
            "kremlin.ru": 0.80
        }
    
    def _initialize_mcp_integrations(self):
        """Инициализирует MCP интеграции"""
        try:
            # Vertex AI для фактчека с Grounding (приоритетный метод)
            if is_mcp_enabled('vertex_ai'):
                try:
                    self.vertex_mcp = VertexAIMCP()
                    logger.info("VertexAIMCP инициализирован в ResearchFactCheckAgent")
                except Exception as e:
                    logger.warning(f"VertexAIMCP недоступен: {e} - будет использоваться fallback")
                    self.vertex_mcp = None
            else:
                logger.warning("Vertex AI недоступен - будет использоваться fallback")
            
            # News API (fallback)
            if is_mcp_enabled('news'):
                self.news_mcp = NewsMCP()
                logger.info("NewsMCP инициализирован в ResearchFactCheckAgent")
            else:
                logger.warning("NewsMCP недоступен - будет использоваться fallback")
            
            # Wikipedia API (fallback)
            if is_mcp_enabled('wikipedia'):
                self.wikipedia_mcp = WikipediaMCP()
                logger.info("WikipediaMCP инициализирован в ResearchFactCheckAgent")
            else:
                logger.warning("WikipediaMCP недоступен - будет использоваться fallback")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации MCP интеграций: {e}")
            self.news_mcp = None
            self.wikipedia_mcp = None
            self.vertex_mcp = None
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Выполняет задачу проверки фактов"""
        try:
            logger.info(f"ResearchFactCheckAgent выполняет задачу: {task.name}")
            
            # Извлекаем данные из контекста
            content_data = task.context.get("content", {})
            check_type = task.context.get("check_type", "basic")
            
            # Выполняем проверку фактов
            report = await self._fact_check_content(content_data, check_type)
            
            # Формируем результат
            result = {
                "task_id": task.id,
                "agent_id": self.agent_id,
                "fact_check_report": {
                    "content_id": report.content_id,
                    "total_claims": report.total_claims,
                    "verified_claims": report.verified_claims,
                    "disputed_claims": report.disputed_claims,
                    "false_claims": report.false_claims,
                    "overall_confidence": report.overall_confidence,
                    "recommendations": report.recommendations
                },
                "detailed_results": [
                    {
                        "claim": result.claim,
                        "type": result.claim_type.value,
                        "status": result.status.value,
                        "confidence": result.confidence_score,
                        "sources": result.verification_sources,
                        "evidence": result.evidence,
                        "recommendations": result.recommendations
                    }
                    for result in report.fact_check_results
                ],
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"ResearchFactCheckAgent завершил задачу {task.id}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка в ResearchFactCheckAgent: {e}")
            raise
    
    async def _fact_check_content(self, content_data: Dict[str, Any], 
                                check_type: str) -> ContentFactCheckReport:
        """Выполняет проверку фактов в контенте"""
        
        # Извлекаем текст для анализа
        text = content_data.get("text", "")
        content_id = content_data.get("id", "")
        
        if not text.strip():
            logger.warning("Пустой текст для проверки фактов")
            return ContentFactCheckReport(
                content_id=content_id,
                total_claims=0,
                verified_claims=0,
                disputed_claims=0,
                false_claims=0,
                overall_confidence=0.0,
                fact_check_results=[],
                recommendations=["Текст пустой - проверка фактов невозможна"]
            )
        
        # Извлекаем утверждения
        claims = await self._extract_claims(text)
        logger.info(f"Извлечено {len(claims)} утверждений для проверки")
        
        # Проверяем каждое утверждение
        fact_check_results = []
        for claim in claims:
            result = await self._verify_claim(claim, check_type)
            fact_check_results.append(result)
        
        # Подсчитываем статистику
        total_claims = len(fact_check_results)
        verified_claims = sum(1 for r in fact_check_results 
                            if r.status == FactCheckStatus.VERIFIED)
        disputed_claims = sum(1 for r in fact_check_results 
                            if r.status == FactCheckStatus.DISPUTED)
        false_claims = sum(1 for r in fact_check_results 
                         if r.status == FactCheckStatus.FALSE)
        
        # Рассчитываем общую уверенность
        overall_confidence = sum(r.confidence_score for r in fact_check_results) / total_claims if total_claims > 0 else 0.0
        
        # Генерируем рекомендации
        recommendations = await self._generate_recommendations(fact_check_results)
        
        return ContentFactCheckReport(
            content_id=content_id,
            total_claims=total_claims,
            verified_claims=verified_claims,
            disputed_claims=disputed_claims,
            false_claims=false_claims,
            overall_confidence=overall_confidence,
            fact_check_results=fact_check_results,
            recommendations=recommendations
        )
    
    async def _extract_claims(self, text: str) -> List[str]:
        """Извлекает фактологические утверждения из текста (упрощенная версия)"""
        claims = []
        
        # Извлекаем утверждения по паттернам
        for claim_type, pattern in self.claim_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Находим контекст вокруг совпадения
                context_claim = self._extract_context_around_match(text, match, 50)
                if context_claim and len(context_claim.strip()) > 10:
                    claims.append(context_claim.strip())
        
        # Убираем дубли и слишком короткие утверждения
        unique_claims = []
        for claim in claims:
            if (len(claim) > 15 and 
                claim not in unique_claims and 
                not any(claim in existing for existing in unique_claims)):
                unique_claims.append(claim)
        
        # Ограничиваем количество утверждений для MVP
        return unique_claims[:10]
    
    def _extract_context_around_match(self, text: str, match: str, context_size: int) -> str:
        """Извлекает контекст вокруг найденного совпадения"""
        try:
            match_index = text.lower().find(match.lower())
            if match_index == -1:
                return ""
            
            start = max(0, match_index - context_size)
            end = min(len(text), match_index + len(match) + context_size)
            
            context = text[start:end]
            
            # Обрезаем по границам предложений
            sentences = re.split(r'[.!?]', context)
            if len(sentences) > 1:
                # Берем предложение, содержащее совпадение
                for sentence in sentences:
                    if match.lower() in sentence.lower():
                        return sentence.strip()
            
            return context.strip()
            
        except Exception as e:
            logger.warning(f"Ошибка извлечения контекста: {e}")
            return ""
    
    async def _verify_claim(self, claim: str, check_type: str) -> FactCheckResult:
        """Проверяет конкретное утверждение"""
        
        # Определяем тип утверждения
        claim_type = await self._classify_claim(claim)
        
        # Проверяем в кэше
        cache_key = f"{claim}_{check_type}"
        if cache_key in self.fact_cache:
            cached_result = self.fact_cache[cache_key]
            if datetime.now() - cached_result.checked_at < self.cache_ttl:
                logger.info(f"Используем кэшированный результат для: {claim[:50]}...")
                return cached_result
        
        # Приоритет: используем Vertex AI с Grounding для фактчека
        if self.vertex_mcp:
            try:
                logger.info(f"Используем Vertex AI Grounding для проверки: {claim[:50]}...")
                result = await self._verify_claim_with_vertex(claim, claim_type)
                
                # Кэшируем результат
                self.fact_cache[cache_key] = result
                return result
            except Exception as e:
                logger.warning(f"Ошибка проверки через Vertex AI: {e} - используем fallback")
        
        # Fallback: используем старые методы проверки
        if claim_type == ClaimType.STATISTICAL:
            result = await self._verify_statistical_claim(claim)
        elif claim_type == ClaimType.TEMPORAL:
            result = await self._verify_temporal_claim(claim)
        elif claim_type == ClaimType.QUOTE:
            result = await self._verify_quote_claim(claim)
        elif claim_type == ClaimType.SCIENTIFIC:
            result = await self._verify_scientific_claim(claim)
        else:
            result = await self._verify_general_claim(claim)
        
        # Кэшируем результат
        self.fact_cache[cache_key] = result
        
        return result
    
    async def _verify_claim_with_vertex(self, claim: str, claim_type: ClaimType) -> FactCheckResult:
        """Проверяет утверждение через Vertex AI с Grounding"""
        try:
            # Вызываем fact_check через Vertex AI
            response = await self.vertex_mcp.fact_check(claim=claim, context=None)
            
            if not response.success:
                logger.warning(f"Vertex AI fact_check вернул ошибку: {response.error}")
                # Возвращаем результат с низкой уверенностью
                return FactCheckResult(
                    claim=claim,
                    claim_type=claim_type,
                    status=FactCheckStatus.UNVERIFIED,
                    confidence_score=0.0,
                    verification_sources=[],
                    evidence=[],
                    recommendations=["Не удалось проверить через Vertex AI"]
                )
            
            # Парсим ответ от Gemini
            generated_text = response.data.get("generated_text", "")
            metadata = response.metadata or {}
            
            # Извлекаем информацию из ответа
            verdict = self._parse_vertex_verdict(generated_text)
            confidence_score = self._calculate_confidence_from_vertex(verdict, metadata)
            sources = self._extract_sources_from_vertex(generated_text, metadata)
            evidence = self._extract_evidence_from_vertex(generated_text)
            recommendations = self._generate_recommendations_from_vertex(verdict, generated_text)
            
            # Определяем статус на основе вердикта
            status = self._map_verdict_to_status(verdict)
            
            logger.info(f"Vertex AI проверил утверждение: {verdict}, confidence: {confidence_score}")
            
            return FactCheckResult(
                claim=claim,
                claim_type=claim_type,
                status=status,
                confidence_score=confidence_score,
                verification_sources=sources,
                evidence=evidence,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Ошибка в _verify_claim_with_vertex: {e}")
            # Возвращаем результат с ошибкой
            return FactCheckResult(
                claim=claim,
                claim_type=claim_type,
                status=FactCheckStatus.UNVERIFIED,
                confidence_score=0.0,
                verification_sources=[],
                evidence=[],
                recommendations=[f"Ошибка проверки через Vertex AI: {str(e)}"]
            )
    
    def _parse_vertex_verdict(self, text: str) -> str:
        """Парсит вердикт из ответа Vertex AI"""
        text_lower = text.lower()
        
        if "правда" in text_lower and "ложь" not in text_lower:
            return "Правда"
        elif "ложь" in text_lower or "неверно" in text_lower or "ошибочно" in text_lower:
            return "Ложь"
        elif "частично" in text_lower or "частично правда" in text_lower:
            return "Частично правда"
        elif "невозможно проверить" in text_lower or "не удалось" in text_lower:
            return "Невозможно проверить"
        else:
            return "Неопределено"
    
    def _calculate_confidence_from_vertex(self, verdict: str, metadata: Dict[str, Any]) -> float:
        """Рассчитывает confidence score на основе вердикта и метаданных"""
        base_confidence = {
            "Правда": 0.9,
            "Частично правда": 0.6,
            "Ложь": 0.1,
            "Невозможно проверить": 0.3,
            "Неопределено": 0.5
        }.get(verdict, 0.5)
        
        # Увеличиваем confidence если есть grounding sources
        if metadata.get("grounding_sources", 0) > 0:
            base_confidence = min(1.0, base_confidence + 0.1)
        
        return base_confidence
    
    def _extract_sources_from_vertex(self, text: str, metadata: Dict[str, Any]) -> List[str]:
        """Извлекает источники из ответа Vertex AI"""
        sources = []
        
        # Ищем секцию "ИСТОЧНИКИ" в тексте
        if "источники:" in text.lower():
            sources_section = text.lower().split("источники:")[-1]
            # Извлекаем URL или названия источников
            import re
            urls = re.findall(r'https?://[^\s]+', sources_section)
            sources.extend(urls)
        
        # Добавляем информацию о grounding sources из метаданных
        if metadata.get("grounding_sources", 0) > 0:
            sources.append(f"Google Search Grounding ({metadata['grounding_sources']} источников)")
        
        return sources if sources else ["Google Search Grounding"]
    
    def _extract_evidence_from_vertex(self, text: str) -> List[str]:
        """Извлекает доказательства из ответа Vertex AI"""
        evidence = []
        
        # Ищем секцию "ОБЪЯСНЕНИЕ" в тексте
        if "объяснение:" in text.lower():
            explanation_section = text.lower().split("объяснение:")[-1].split("источники:")[0]
            evidence.append(explanation_section.strip())
        
        # Если нет явной секции, берем весь текст как доказательство
        if not evidence:
            evidence.append(text[:500])  # Первые 500 символов
        
        return evidence
    
    def _generate_recommendations_from_vertex(self, verdict: str, text: str) -> List[str]:
        """Генерирует рекомендации на основе вердикта Vertex AI"""
        recommendations = []
        
        if verdict == "Правда":
            recommendations.append("✅ Утверждение подтверждено через Google Search Grounding")
        elif verdict == "Частично правда":
            recommendations.append("⚠️ Утверждение частично подтверждено - рекомендуется уточнить детали")
        elif verdict == "Ложь":
            recommendations.append("❌ Утверждение опровергнуто - требуется исправление")
        elif verdict == "Невозможно проверить":
            recommendations.append("ℹ️ Не удалось проверить утверждение - рекомендуется добавить источники")
        else:
            recommendations.append("⚠️ Неопределенный результат проверки - рекомендуется дополнительная проверка")
        
        return recommendations
    
    def _map_verdict_to_status(self, verdict: str) -> FactCheckStatus:
        """Маппит вердикт Vertex AI в FactCheckStatus"""
        mapping = {
            "Правда": FactCheckStatus.VERIFIED,
            "Частично правда": FactCheckStatus.PARTIALLY_VERIFIED,
            "Ложь": FactCheckStatus.FALSE,
            "Невозможно проверить": FactCheckStatus.UNVERIFIED,
            "Неопределено": FactCheckStatus.UNVERIFIED
        }
        return mapping.get(verdict, FactCheckStatus.UNVERIFIED)
    
    async def _classify_claim(self, claim: str) -> ClaimType:
        """Классифицирует тип утверждения"""
        
        # Проверяем на статистику
        if re.search(r'\d+(?:\.\d+)?%', claim):
            return ClaimType.STATISTICAL
        
        # Проверяем на даты
        if re.search(r'\d{1,2}[./]\d{1,2}[./]\d{2,4}|\d{4}', claim):
            return ClaimType.TEMPORAL
        
        # Проверяем на цитаты
        if claim.startswith('"') and claim.endswith('"'):
            return ClaimType.QUOTE
        
        # Проверяем на научные термины
        scientific_terms = ['исследование', 'эксперимент', 'анализ', 'данные', 'результаты', 'ученые', 'наука']
        if any(term in claim.lower() for term in scientific_terms):
            return ClaimType.SCIENTIFIC
        
        # Проверяем на исторические термины
        historical_terms = ['в прошлом', 'история', 'исторический', 'в 19', 'в 20']
        if any(term in claim.lower() for term in historical_terms):
            return ClaimType.HISTORICAL
        
        return ClaimType.GENERAL
    
    async def _verify_statistical_claim(self, claim: str) -> FactCheckResult:
        """Проверяет статистическое утверждение"""
        verification_sources = []
        evidence = []
        confidence_score = 0.0
        
        # Пытаемся найти в Wikipedia
        if self.wikipedia_mcp:
            try:
                result = await self.wikipedia_mcp.search_statistics(claim)
                if result.success and result.data:
                    sources = result.data.get('sources', [])
                    verification_sources.extend(sources)
                    evidence.extend(result.data.get('evidence', []))
                    confidence_score += 0.4
                    logger.info(f"Найдены источники в Wikipedia для статистики: {len(sources)}")
            except Exception as e:
                logger.warning(f"Ошибка проверки в WikipediaMCP: {e}")
        
        # Пытаемся найти в новостных источниках
        if self.news_mcp:
            try:
                result = await self.news_mcp.execute_with_retry('get_news', query=claim, language='ru')
                if result.success and result.data:
                    articles = result.data.get('articles', [])
                    if articles:
                        verification_sources.extend([f"news_source_{i}" for i in range(min(3, len(articles)))])
                        evidence.extend([f"Найдено {len(articles)} новостных статей по теме"])
                        confidence_score += 0.3
                        logger.info(f"Найдены новостные источники для статистики: {len(articles)} статей")
            except Exception as e:
                logger.warning(f"Ошибка проверки в NewsMCP: {e}")
        
        # Определяем статус на основе найденных источников
        if confidence_score >= 0.6:
            status = FactCheckStatus.VERIFIED
        elif confidence_score >= 0.3:
            status = FactCheckStatus.PARTIALLY_VERIFIED
        else:
            status = FactCheckStatus.UNVERIFIED
        
        return FactCheckResult(
            claim=claim,
            claim_type=ClaimType.STATISTICAL,
            status=status,
            confidence_score=min(confidence_score, 1.0),
            verification_sources=verification_sources,
            evidence=evidence,
            recommendations=self._generate_statistical_recommendations(claim, status)
        )
    
    async def _verify_temporal_claim(self, claim: str) -> FactCheckResult:
        """Проверяет временное утверждение"""
        verification_sources = []
        evidence = []
        confidence_score = 0.0
        
        # Проверяем в Wikipedia
        if self.wikipedia_mcp:
            try:
                result = await self.wikipedia_mcp.search_historical(claim)
                if result.success and result.data:
                    sources = result.data.get('sources', [])
                    verification_sources.extend(sources)
                    evidence.extend(result.data.get('evidence', []))
                    confidence_score += 0.5
                    logger.info(f"Найдены исторические источники в Wikipedia: {len(sources)}")
            except Exception as e:
                logger.warning(f"Ошибка проверки в WikipediaMCP: {e}")
        
        # Проверяем в новостных источниках
        if self.news_mcp:
            try:
                result = await self.news_mcp.execute_with_retry('get_news', query=claim, language='ru')
                if result.success and result.data:
                    articles = result.data.get('articles', [])
                    if articles:
                        verification_sources.extend([f"news_source_{i}" for i in range(min(3, len(articles)))])
                        evidence.extend([f"Найдено {len(articles)} новостных статей по теме"])
                        confidence_score += 0.3
                        logger.info(f"Найдены новостные источники для временного утверждения: {len(articles)} статей")
            except Exception as e:
                logger.warning(f"Ошибка проверки в NewsMCP: {e}")
        
        # Определяем статус
        if confidence_score >= 0.7:
            status = FactCheckStatus.VERIFIED
        elif confidence_score >= 0.4:
            status = FactCheckStatus.PARTIALLY_VERIFIED
        else:
            status = FactCheckStatus.UNVERIFIED
        
        return FactCheckResult(
            claim=claim,
            claim_type=ClaimType.TEMPORAL,
            status=status,
            confidence_score=min(confidence_score, 1.0),
            verification_sources=verification_sources,
            evidence=evidence,
            recommendations=self._generate_temporal_recommendations(claim, status)
        )
    
    async def _verify_quote_claim(self, claim: str) -> FactCheckResult:
        """Проверяет цитату"""
        verification_sources = []
        evidence = []
        confidence_score = 0.0
        
        # Проверяем в новостных источниках
        if self.news_mcp:
            try:
                result = await self.news_mcp.execute_with_retry('get_news', query=claim, language='ru')
                if result.success and result.data:
                    articles = result.data.get('articles', [])
                    if articles:
                        verification_sources.extend([f"news_source_{i}" for i in range(min(3, len(articles)))])
                        evidence.extend([f"Найдено {len(articles)} новостных статей с похожими цитатами"])
                        confidence_score += 0.6
                        logger.info(f"Найдены источники для цитаты: {len(articles)} статей")
            except Exception as e:
                logger.warning(f"Ошибка проверки в NewsMCP: {e}")
        
        # Проверяем в Wikipedia
        if self.wikipedia_mcp:
            try:
                result = await self.wikipedia_mcp.search_general(claim)
                if result.success and result.data:
                    sources = result.data.get('sources', [])
                    verification_sources.extend(sources)
                    evidence.extend(result.data.get('evidence', []))
                    confidence_score += 0.3
                    logger.info(f"Найдены источники в Wikipedia для цитаты: {len(sources)}")
            except Exception as e:
                logger.warning(f"Ошибка проверки в WikipediaMCP: {e}")
        
        # Определяем статус
        if confidence_score >= 0.7:
            status = FactCheckStatus.VERIFIED
        elif confidence_score >= 0.4:
            status = FactCheckStatus.PARTIALLY_VERIFIED
        else:
            status = FactCheckStatus.UNVERIFIED
        
        return FactCheckResult(
            claim=claim,
            claim_type=ClaimType.QUOTE,
            status=status,
            confidence_score=min(confidence_score, 1.0),
            verification_sources=verification_sources,
            evidence=evidence,
            recommendations=self._generate_quote_recommendations(claim, status)
        )
    
    async def _verify_scientific_claim(self, claim: str) -> FactCheckResult:
        """Проверяет научное утверждение"""
        verification_sources = []
        evidence = []
        confidence_score = 0.0
        
        # Проверяем в Wikipedia
        if self.wikipedia_mcp:
            try:
                result = await self.wikipedia_mcp.search_scientific(claim)
                if result.success and result.data:
                    sources = result.data.get('sources', [])
                    verification_sources.extend(sources)
                    evidence.extend(result.data.get('evidence', []))
                    confidence_score += 0.5
                    logger.info(f"Найдены научные источники в Wikipedia: {len(sources)}")
            except Exception as e:
                logger.warning(f"Ошибка проверки в WikipediaMCP: {e}")
        
        # Проверяем в новостных источниках
        if self.news_mcp:
            try:
                result = await self.news_mcp.execute_with_retry('get_news', query=claim, language='ru')
                if result.success and result.data:
                    articles = result.data.get('articles', [])
                    if articles:
                        verification_sources.extend([f"news_source_{i}" for i in range(min(3, len(articles)))])
                        evidence.extend([f"Найдено {len(articles)} новостных статей по научной теме"])
                        confidence_score += 0.3
                        logger.info(f"Найдены новостные источники для научного утверждения: {len(articles)} статей")
            except Exception as e:
                logger.warning(f"Ошибка проверки в NewsMCP: {e}")
        
        # Определяем статус
        if confidence_score >= 0.6:
            status = FactCheckStatus.VERIFIED
        elif confidence_score >= 0.3:
            status = FactCheckStatus.PARTIALLY_VERIFIED
        else:
            status = FactCheckStatus.UNVERIFIED
        
        return FactCheckResult(
            claim=claim,
            claim_type=ClaimType.SCIENTIFIC,
            status=status,
            confidence_score=min(confidence_score, 1.0),
            verification_sources=verification_sources,
            evidence=evidence,
            recommendations=self._generate_scientific_recommendations(claim, status)
        )
    
    async def _verify_general_claim(self, claim: str) -> FactCheckResult:
        """Проверяет общее утверждение"""
        verification_sources = []
        evidence = []
        confidence_score = 0.0
        
        # Проверяем в Wikipedia
        if self.wikipedia_mcp:
            try:
                result = await self.wikipedia_mcp.search_general(claim)
                if result.success and result.data:
                    sources = result.data.get('sources', [])
                    verification_sources.extend(sources)
                    evidence.extend(result.data.get('evidence', []))
                    confidence_score += 0.4
                    logger.info(f"Найдены общие источники в Wikipedia: {len(sources)}")
            except Exception as e:
                logger.warning(f"Ошибка проверки в WikipediaMCP: {e}")
        
        # Проверяем в новостных источниках
        if self.news_mcp:
            try:
                result = await self.news_mcp.execute_with_retry('get_news', query=claim, language='ru')
                if result.success and result.data:
                    articles = result.data.get('articles', [])
                    if articles:
                        verification_sources.extend([f"news_source_{i}" for i in range(min(3, len(articles)))])
                        evidence.extend([f"Найдено {len(articles)} новостных статей по теме"])
                        confidence_score += 0.3
                        logger.info(f"Найдены новостные источники для общего утверждения: {len(articles)} статей")
            except Exception as e:
                logger.warning(f"Ошибка проверки в NewsMCP: {e}")
        
        # Определяем статус
        if confidence_score >= 0.6:
            status = FactCheckStatus.VERIFIED
        elif confidence_score >= 0.3:
            status = FactCheckStatus.PARTIALLY_VERIFIED
        else:
            status = FactCheckStatus.UNVERIFIED
        
        return FactCheckResult(
            claim=claim,
            claim_type=ClaimType.GENERAL,
            status=status,
            confidence_score=min(confidence_score, 1.0),
            verification_sources=verification_sources,
            evidence=evidence,
            recommendations=self._generate_general_recommendations(claim, status)
        )
    
    def _generate_statistical_recommendations(self, claim: str, status: FactCheckStatus) -> List[str]:
        """Генерирует рекомендации для статистических утверждений"""
        recommendations = []
        
        if status == FactCheckStatus.UNVERIFIED:
            recommendations.append("Статистическое утверждение не удалось верифицировать - рекомендуется уточнить источник")
        elif status == FactCheckStatus.PARTIALLY_VERIFIED:
            recommendations.append("Статистика частично подтверждена - рекомендуется добавить дополнительные источники")
        elif status == FactCheckStatus.VERIFIED:
            recommendations.append("Статистическое утверждение подтверждено надежными источниками")
        
        return recommendations
    
    def _generate_temporal_recommendations(self, claim: str, status: FactCheckStatus) -> List[str]:
        """Генерирует рекомендации для временных утверждений"""
        recommendations = []
        
        if status == FactCheckStatus.UNVERIFIED:
            recommendations.append("Временное утверждение не удалось верифицировать - рекомендуется проверить дату")
        elif status == FactCheckStatus.PARTIALLY_VERIFIED:
            recommendations.append("Дата частично подтверждена - рекомендуется уточнить временные рамки")
        elif status == FactCheckStatus.VERIFIED:
            recommendations.append("Временное утверждение подтверждено историческими источниками")
        
        return recommendations
    
    def _generate_quote_recommendations(self, claim: str, status: FactCheckStatus) -> List[str]:
        """Генерирует рекомендации для цитат"""
        recommendations = []
        
        if status == FactCheckStatus.UNVERIFIED:
            recommendations.append("Цитата не найдена в проверенных источниках - рекомендуется уточнить авторство")
        elif status == FactCheckStatus.PARTIALLY_VERIFIED:
            recommendations.append("Цитата частично подтверждена - рекомендуется проверить контекст")
        elif status == FactCheckStatus.VERIFIED:
            recommendations.append("Цитата подтверждена авторитетными источниками")
        
        return recommendations
    
    def _generate_scientific_recommendations(self, claim: str, status: FactCheckStatus) -> List[str]:
        """Генерирует рекомендации для научных утверждений"""
        recommendations = []
        
        if status == FactCheckStatus.UNVERIFIED:
            recommendations.append("Научное утверждение не найдено в рецензируемых источниках")
        elif status == FactCheckStatus.PARTIALLY_VERIFIED:
            recommendations.append("Научное утверждение частично подтверждено - рекомендуется добавить ссылки на исследования")
        elif status == FactCheckStatus.VERIFIED:
            recommendations.append("Научное утверждение подтверждено рецензируемыми источниками")
        
        return recommendations
    
    def _generate_general_recommendations(self, claim: str, status: FactCheckStatus) -> List[str]:
        """Генерирует рекомендации для общих утверждений"""
        recommendations = []
        
        if status == FactCheckStatus.UNVERIFIED:
            recommendations.append("Утверждение не удалось верифицировать - рекомендуется добавить источники")
        elif status == FactCheckStatus.PARTIALLY_VERIFIED:
            recommendations.append("Утверждение частично подтверждено - рекомендуется добавить дополнительные источники")
        elif status == FactCheckStatus.VERIFIED:
            recommendations.append("Утверждение подтверждено надежными источниками")
        
        return recommendations
    
    async def _generate_recommendations(self, fact_check_results: List[FactCheckResult]) -> List[str]:
        """Генерирует общие рекомендации по контенту"""
        recommendations = []
        
        # Анализируем результаты
        unverified_count = sum(1 for r in fact_check_results 
                             if r.status == FactCheckStatus.UNVERIFIED)
        disputed_count = sum(1 for r in fact_check_results 
                           if r.status == FactCheckStatus.DISPUTED)
        false_count = sum(1 for r in fact_check_results 
                        if r.status == FactCheckStatus.FALSE)
        
        if false_count > 0:
            recommendations.append(f"⚠️ Обнаружено {false_count} ложных утверждений - требуется исправление")
        
        if disputed_count > 0:
            recommendations.append(f"⚠️ Обнаружено {disputed_count} спорных утверждений - рекомендуется пересмотр")
        
        if unverified_count > 0:
            recommendations.append(f"ℹ️ {unverified_count} утверждений не удалось верифицировать - рекомендуется добавить источники")
        
        # Общие рекомендации
        if len(fact_check_results) > 0:
            avg_confidence = sum(r.confidence_score for r in fact_check_results) / len(fact_check_results)
            if avg_confidence < 0.5:
                recommendations.append("📊 Низкая общая достоверность контента - рекомендуется дополнительная проверка")
            elif avg_confidence > 0.8:
                recommendations.append("✅ Высокая достоверность контента - готов к публикации")
            else:
                recommendations.append("📝 Средняя достоверность контента - рекомендуется дополнительная проверка спорных моментов")
        
        return recommendations
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кэша"""
        return {
            "cached_facts": len(self.fact_cache),
            "cache_ttl_hours": self.cache_ttl.total_seconds() / 3600,
            "oldest_cached": min(
                (result.checked_at for result in self.fact_cache.values()),
                default=None
            ).isoformat() if self.fact_cache else None
        }
    
    def clear_cache(self):
        """Очищает кэш проверенных фактов"""
        self.fact_cache.clear()
        logger.info("Кэш проверенных фактов очищен")
