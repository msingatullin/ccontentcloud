"""
LegalGuardAgent - Агент юридической проверки контента
Проверяет контент на юридические риски и соответствие законодательству РФ
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.orchestrator.agent_manager import BaseAgent, AgentCapability, AgentStatus
from app.orchestrator.workflow_engine import TaskType, Task

# Настройка логирования
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Уровни юридических рисков"""
    CRITICAL = "critical"    # Требует обязательного вмешательства человека
    HIGH = "high"           # Требует добавления дисклеймеров
    MEDIUM = "medium"       # Рекомендации по улучшению
    LOW = "low"             # Контент безопасен


class LegalDomain(Enum):
    """Юридические области"""
    FINANCIAL = "financial"           # Финансовые услуги и инвестиции
    MEDICAL = "medical"              # Медицинские советы
    ADVERTISING = "advertising"       # Реклама товаров и услуг
    PERSONAL_DATA = "personal_data"   # Персональные данные
    COPYRIGHT = "copyright"          # Авторские права и цитирование
    GENERAL = "general"              # Общие правовые вопросы


@dataclass
class LegalRisk:
    """Юридический риск"""
    risk_id: str
    level: RiskLevel
    domain: LegalDomain
    description: str
    content_excerpt: str
    line_number: Optional[int] = None
    suggested_action: str = ""
    disclaimer_text: Optional[str] = None
    legal_basis: str = ""
    confidence_score: float = 0.0


@dataclass
class LegalComplianceReport:
    """Отчет о юридическом соответствии"""
    content_id: str
    overall_risk_level: RiskLevel
    risks: List[LegalRisk]
    disclaimers_added: List[str]
    recommendations: List[str]
    compliance_score: float
    requires_human_review: bool
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class LegalRule:
    """Правовое правило"""
    rule_id: str
    domain: LegalDomain
    pattern: str
    risk_level: RiskLevel
    description: str
    action_required: str
    disclaimer_template: Optional[str] = None
    legal_basis: str = ""


class LegalGuardAgent(BaseAgent):
    """Агент для юридической проверки контента"""
    
    def __init__(self, agent_id: str = "legal_guard_agent"):
        capability = AgentCapability(
            task_types=[TaskType.PLANNED],  # Требует тщательного анализа
            max_concurrent_tasks=2,         # Медленная, но тщательная проверка
            specializations=["legal_compliance", "disclaimers", "risk_assessment", "advertising_law"],
            performance_score=0.7           # Медленнее из-за тщательной проверки
        )
        super().__init__(agent_id, "Legal Guard Agent", capability)
        
        # Правовые правила и паттерны
        self.legal_rules = self._load_legal_rules()
        self.risk_patterns = self._load_risk_patterns()
        self.disclaimer_templates = self._load_disclaimer_templates()
        
        # Кэш проверок (в памяти для MVP)
        self.compliance_cache = {}
        self.cache_ttl = timedelta(hours=6)  # Кэш на 6 часов
        
        # Настройки проверки
        self.risk_thresholds = {
            'critical_threshold': 0.9,
            'high_threshold': 0.7,
            'medium_threshold': 0.5,
            'low_threshold': 0.3
        }
        
        # Статистика проверок
        self.check_stats = {
            'total_checks': 0,
            'critical_risks': 0,
            'high_risks': 0,
            'medium_risks': 0,
            'low_risks': 0
        }
        
        logger.info(f"LegalGuardAgent {agent_id} инициализирован")
    
    def _load_legal_rules(self) -> Dict[LegalDomain, List[LegalRule]]:
        """Загружает правовые правила для разных областей"""
        rules = {
            LegalDomain.FINANCIAL: [
                LegalRule(
                    rule_id="fin_investment_advice",
                    domain=LegalDomain.FINANCIAL,
                    pattern=r"(инвест|акци|облигаци|фонд|трейд|криптовалют)",
                    risk_level=RiskLevel.HIGH,
                    description="Финансовые советы требуют дисклеймера",
                    action_required="add_disclaimer",
                    disclaimer_template="Инвестиции связаны с рисками. Не является инвестиционной рекомендацией.",
                    legal_basis="ФЗ 'О рынке ценных бумаг'"
                ),
                LegalRule(
                    rule_id="fin_guaranteed_returns",
                    domain=LegalDomain.FINANCIAL,
                    pattern=r"(гарантированн|100%|без риска|стабильн)",
                    risk_level=RiskLevel.CRITICAL,
                    description="Гарантии доходности запрещены",
                    action_required="human_review",
                    legal_basis="ФЗ 'О рекламе' ст. 7"
                )
            ],
            LegalDomain.MEDICAL: [
                LegalRule(
                    rule_id="med_health_advice",
                    domain=LegalDomain.MEDICAL,
                    pattern=r"(лечен|лекарств|диагноз|симптом|болезн)",
                    risk_level=RiskLevel.HIGH,
                    description="Медицинские советы требуют предупреждения",
                    action_required="add_disclaimer",
                    disclaimer_template="Не является медицинской консультацией. Обратитесь к врачу.",
                    legal_basis="ФЗ 'Об основах охраны здоровья граждан'"
                ),
                LegalRule(
                    rule_id="med_drug_promotion",
                    domain=LegalDomain.MEDICAL,
                    pattern=r"(препарат|таблетк|лекарств).*(реклам|покупай|закажи)",
                    risk_level=RiskLevel.CRITICAL,
                    description="Реклама лекарств запрещена",
                    action_required="human_review",
                    legal_basis="ФЗ 'О рекламе' ст. 24"
                )
            ],
            LegalDomain.ADVERTISING: [
                LegalRule(
                    rule_id="adv_misleading",
                    domain=LegalDomain.ADVERTISING,
                    pattern=r"(лучш|единственн|только у нас|эксклюзивн)",
                    risk_level=RiskLevel.MEDIUM,
                    description="Потенциально вводящие в заблуждение утверждения",
                    action_required="review",
                    legal_basis="ФЗ 'О рекламе' ст. 5"
                ),
                LegalRule(
                    rule_id="adv_comparison",
                    domain=LegalDomain.ADVERTISING,
                    pattern=r"(лучше чем|превосход|обгоня)",
                    risk_level=RiskLevel.MEDIUM,
                    description="Сравнительная реклама требует обоснования",
                    action_required="review",
                    legal_basis="ФЗ 'О рекламе' ст. 6"
                )
            ],
            LegalDomain.PERSONAL_DATA: [
                LegalRule(
                    rule_id="pd_collection",
                    domain=LegalDomain.PERSONAL_DATA,
                    pattern=r"(собираем|обрабатываем|храним).*(данн|информац)",
                    risk_level=RiskLevel.HIGH,
                    description="Обработка персональных данных требует согласия",
                    action_required="add_disclaimer",
                    disclaimer_template="Обработка персональных данных в соответствии с 152-ФЗ",
                    legal_basis="152-ФЗ 'О персональных данных'"
                )
            ],
            LegalDomain.COPYRIGHT: [
                LegalRule(
                    rule_id="copyright_quotes",
                    domain=LegalDomain.COPYRIGHT,
                    pattern=r"\"[^\"]{50,}\"",
                    risk_level=RiskLevel.MEDIUM,
                    description="Длинные цитаты могут нарушать авторские права",
                    action_required="review",
                    legal_basis="ГК РФ ст. 1274"
                )
            ]
        }
        return rules
    
    def _load_risk_patterns(self) -> Dict[str, str]:
        """Загружает паттерны для выявления рисков"""
        return {
            "financial_keywords": r"(инвест|акци|облигаци|фонд|трейд|криптовалют|биткоин|эфир)",
            "medical_keywords": r"(лечен|лекарств|диагноз|симптом|болезн|здоровь|медицин)",
            "advertising_keywords": r"(реклам|покупай|закажи|скидк|акци|распродаж)",
            "guarantee_keywords": r"(гарантированн|100%|без риска|стабильн|надежн)",
            "comparison_keywords": r"(лучше чем|превосход|обгоня|единственн|только у нас)",
            "personal_data_keywords": r"(собираем|обрабатываем|храним|персональн|данн)"
        }
    
    def _load_disclaimer_templates(self) -> Dict[LegalDomain, str]:
        """Загружает шаблоны дисклеймеров"""
        return {
            LegalDomain.FINANCIAL: "⚠️ Инвестиции связаны с рисками. Не является инвестиционной рекомендацией. Обратитесь к финансовому консультанту.",
            LegalDomain.MEDICAL: "⚠️ Не является медицинской консультацией. При проблемах со здоровьем обратитесь к врачу.",
            LegalDomain.ADVERTISING: "⚠️ Реклама. ООО 'Компания' не несет ответственности за результаты использования.",
            LegalDomain.PERSONAL_DATA: "ℹ️ Обработка персональных данных в соответствии с 152-ФЗ 'О персональных данных'.",
            LegalDomain.COPYRIGHT: "ℹ️ Материал представлен в ознакомительных целях. Все права принадлежат авторам."
        }
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Выполняет задачу по юридической проверке контента"""
        try:
            self.status = AgentStatus.BUSY
            self.last_activity = datetime.now()
            
            task_data = task.context
            content_text = task_data.get("content", "")
            content_id = task_data.get("content_id", task.id)
            content_type = task_data.get("content_type", "text")
            
            # Проверяем кэш
            cache_key = f"{content_id}_{hash(content_text)}"
            if cache_key in self.compliance_cache:
                cached_result = self.compliance_cache[cache_key]
                if datetime.now() - cached_result['timestamp'] < self.cache_ttl:
                    logger.info(f"Используем кэшированный результат для {content_id}")
                    return cached_result['report']
            
            # Выполняем юридическую проверку
            report = await self._analyze_legal_compliance(
                content_text, content_id, content_type
            )
            
            # Сохраняем в кэш
            self.compliance_cache[cache_key] = {
                'report': report,
                'timestamp': datetime.now()
            }
            
            # Обновляем статистику
            self._update_check_stats(report)
            
            self.status = AgentStatus.IDLE
            self.completed_tasks.append(task.id)
            
            logger.info(f"Юридическая проверка завершена для {content_id}. Риск: {report['overall_risk_level']}")
            
            return report
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении юридической проверки: {e}")
            self.status = AgentStatus.ERROR
            self.error_count += 1
            raise
    
    async def _analyze_legal_compliance(self, content: str, content_id: str, content_type: str) -> Dict[str, Any]:
        """Анализирует контент на юридическое соответствие"""
        risks = []
        disclaimers_added = []
        recommendations = []
        
        # Разбиваем контент на строки для анализа
        lines = content.split('\n')
        
        # Проверяем каждое правило
        for domain, rules in self.legal_rules.items():
            for rule in rules:
                matches = re.finditer(rule.pattern, content, re.IGNORECASE)
                for match in matches:
                    # Находим номер строки
                    line_number = content[:match.start()].count('\n') + 1
                    
                    # Создаем риск
                    risk = LegalRisk(
                        risk_id=f"{rule.rule_id}_{len(risks)}",
                        level=rule.risk_level,
                        domain=domain,
                        description=rule.description,
                        content_excerpt=match.group(),
                        line_number=line_number,
                        suggested_action=rule.action_required,
                        disclaimer_text=rule.disclaimer_template,
                        legal_basis=rule.legal_basis,
                        confidence_score=self._calculate_confidence_score(match, rule)
                    )
                    risks.append(risk)
                    
                    # Добавляем дисклеймер если требуется
                    if rule.action_required == "add_disclaimer" and rule.disclaimer_template:
                        disclaimers_added.append(rule.disclaimer_template)
                    
                    # Добавляем рекомендации
                    if rule.action_required == "review":
                        recommendations.append(f"Проверить: {rule.description}")
        
        # Определяем общий уровень риска
        overall_risk_level = self._determine_overall_risk_level(risks)
        
        # Вычисляем общий балл соответствия
        compliance_score = self._calculate_compliance_score(risks)
        
        # Определяем, требуется ли человеческая проверка
        requires_human_review = any(risk.level == RiskLevel.CRITICAL for risk in risks)
        
        report = {
            "content_id": content_id,
            "overall_risk_level": overall_risk_level.value,
            "risks": [
                {
                    "risk_id": risk.risk_id,
                    "level": risk.level.value,
                    "domain": risk.domain.value,
                    "description": risk.description,
                    "content_excerpt": risk.content_excerpt,
                    "line_number": risk.line_number,
                    "suggested_action": risk.suggested_action,
                    "disclaimer_text": risk.disclaimer_text,
                    "legal_basis": risk.legal_basis,
                    "confidence_score": risk.confidence_score
                }
                for risk in risks
            ],
            "disclaimers_added": disclaimers_added,
            "recommendations": recommendations,
            "compliance_score": compliance_score,
            "requires_human_review": requires_human_review,
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def _calculate_confidence_score(self, match, rule: LegalRule) -> float:
        """Вычисляет уровень уверенности в обнаружении риска"""
        base_score = 0.7
        
        # Увеличиваем уверенность для точных совпадений
        if match.group().lower() in rule.pattern.lower():
            base_score += 0.2
        
        # Увеличиваем уверенность для критических рисков
        if rule.risk_level == RiskLevel.CRITICAL:
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _determine_overall_risk_level(self, risks: List[LegalRisk]) -> RiskLevel:
        """Определяет общий уровень риска"""
        if not risks:
            return RiskLevel.LOW
        
        # Берем максимальный уровень риска
        max_risk = max(risks, key=lambda r: self._risk_level_priority(r.level))
        return max_risk.level
    
    def _risk_level_priority(self, level: RiskLevel) -> int:
        """Возвращает приоритет уровня риска (больше = выше приоритет)"""
        priorities = {
            RiskLevel.CRITICAL: 4,
            RiskLevel.HIGH: 3,
            RiskLevel.MEDIUM: 2,
            RiskLevel.LOW: 1
        }
        return priorities.get(level, 0)
    
    def _calculate_compliance_score(self, risks: List[LegalRisk]) -> float:
        """Вычисляет общий балл соответствия (0-100)"""
        if not risks:
            return 100.0
        
        # Штрафы за разные уровни рисков
        penalties = {
            RiskLevel.CRITICAL: 50,
            RiskLevel.HIGH: 30,
            RiskLevel.MEDIUM: 15,
            RiskLevel.LOW: 5
        }
        
        total_penalty = sum(penalties.get(risk.level, 0) for risk in risks)
        score = max(0, 100 - total_penalty)
        
        return round(score, 1)
    
    def _update_check_stats(self, report: Dict[str, Any]):
        """Обновляет статистику проверок"""
        self.check_stats['total_checks'] += 1
        
        risk_level = report['overall_risk_level']
        if risk_level == 'critical':
            self.check_stats['critical_risks'] += 1
        elif risk_level == 'high':
            self.check_stats['high_risks'] += 1
        elif risk_level == 'medium':
            self.check_stats['medium_risks'] += 1
        elif risk_level == 'low':
            self.check_stats['low_risks'] += 1
    
    async def get_legal_advice(self, question: str) -> Dict[str, Any]:
        """Предоставляет юридическую консультацию (базовая версия)"""
        # Базовая система ответов на юридические вопросы
        legal_qa = {
            "реклама": "Реклама должна соответствовать ФЗ 'О рекламе'. Избегайте вводящих в заблуждение утверждений.",
            "персональные данные": "Обработка персональных данных регулируется 152-ФЗ. Требуется согласие субъекта.",
            "авторские права": "Цитирование допускается в объеме, оправданном целью цитирования (ГК РФ ст. 1274).",
            "медицинская реклама": "Реклама лекарств запрещена. Медицинские советы требуют предупреждения.",
            "финансовые услуги": "Финансовые советы требуют дисклеймера о рисках инвестиций."
        }
        
        # Простой поиск по ключевым словам
        for keyword, answer in legal_qa.items():
            if keyword.lower() in question.lower():
                return {
                    "question": question,
                    "answer": answer,
                    "confidence": 0.8,
                    "source": "База знаний Legal Guard Agent",
                    "timestamp": datetime.now().isoformat()
                }
        
        return {
            "question": question,
            "answer": "Для получения точной юридической консультации обратитесь к юристу.",
            "confidence": 0.3,
            "source": "Общий ответ",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_check_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику проверок"""
        total = self.check_stats['total_checks']
        if total == 0:
            return {"message": "Проверки еще не проводились"}
        
        return {
            "total_checks": total,
            "risk_distribution": {
                "critical": self.check_stats['critical_risks'],
                "high": self.check_stats['high_risks'],
                "medium": self.check_stats['medium_risks'],
                "low": self.check_stats['low_risks']
            },
            "risk_percentages": {
                "critical": round(self.check_stats['critical_risks'] / total * 100, 1),
                "high": round(self.check_stats['high_risks'] / total * 100, 1),
                "medium": round(self.check_stats['medium_risks'] / total * 100, 1),
                "low": round(self.check_stats['low_risks'] / total * 100, 1)
            },
            "cache_size": len(self.compliance_cache),
            "last_activity": self.last_activity.isoformat()
        }
