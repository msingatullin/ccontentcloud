"""
Конфигурация для Legal Guard Agent
Настройки юридических правил и параметров проверки
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from .legal_guard_agent import RiskLevel, LegalDomain


@dataclass
class LegalRuleConfig:
    """Конфигурация правового правила"""
    enabled: bool = True
    severity_multiplier: float = 1.0
    custom_disclaimer: Optional[str] = None
    additional_checks: List[str] = field(default_factory=list)


@dataclass
class DomainConfig:
    """Конфигурация для юридической области"""
    enabled: bool = True
    risk_threshold: float = 0.5
    auto_disclaimer: bool = True
    require_human_review: bool = False
    custom_rules: List[str] = field(default_factory=list)


@dataclass
class CacheConfig:
    """Конфигурация кэширования"""
    enabled: bool = True
    ttl_hours: int = 6
    max_size: int = 1000
    cleanup_interval_hours: int = 24


@dataclass
class LegalAgentConfig:
    """Основная конфигурация Legal Guard Agent"""
    agent_name: str = "Legal Guard Agent"
    max_concurrent_tasks: int = 2
    performance_score: float = 0.7
    
    # Настройки проверки
    enable_auto_disclaimers: bool = True
    enable_human_review_requests: bool = True
    strict_mode: bool = False
    
    # Пороги рисков
    risk_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'critical_threshold': 0.9,
        'high_threshold': 0.7,
        'medium_threshold': 0.5,
        'low_threshold': 0.3
    })
    
    # Конфигурация областей
    domain_configs: Dict[LegalDomain, DomainConfig] = field(default_factory=dict)
    
    # Конфигурация правил
    rule_configs: Dict[str, LegalRuleConfig] = field(default_factory=dict)
    
    # Кэширование
    cache: CacheConfig = field(default_factory=CacheConfig)
    
    # Дополнительные настройки
    enable_statistics: bool = True
    log_detailed_reports: bool = False
    enable_legal_qa: bool = True


def load_config_from_env() -> LegalAgentConfig:
    """Загружает конфигурацию из переменных окружения"""
    
    # Создаем конфигурации для областей
    domain_configs = {
        LegalDomain.FINANCIAL: DomainConfig(
            enabled=os.getenv("LEGAL_FINANCIAL_ENABLED", "true").lower() == "true",
            risk_threshold=float(os.getenv("LEGAL_FINANCIAL_THRESHOLD", "0.7")),
            auto_disclaimer=os.getenv("LEGAL_FINANCIAL_AUTO_DISCLAIMER", "true").lower() == "true",
            require_human_review=os.getenv("LEGAL_FINANCIAL_HUMAN_REVIEW", "false").lower() == "true"
        ),
        LegalDomain.MEDICAL: DomainConfig(
            enabled=os.getenv("LEGAL_MEDICAL_ENABLED", "true").lower() == "true",
            risk_threshold=float(os.getenv("LEGAL_MEDICAL_THRESHOLD", "0.8")),
            auto_disclaimer=os.getenv("LEGAL_MEDICAL_AUTO_DISCLAIMER", "true").lower() == "true",
            require_human_review=os.getenv("LEGAL_MEDICAL_HUMAN_REVIEW", "true").lower() == "true"
        ),
        LegalDomain.ADVERTISING: DomainConfig(
            enabled=os.getenv("LEGAL_ADVERTISING_ENABLED", "true").lower() == "true",
            risk_threshold=float(os.getenv("LEGAL_ADVERTISING_THRESHOLD", "0.6")),
            auto_disclaimer=os.getenv("LEGAL_ADVERTISING_AUTO_DISCLAIMER", "false").lower() == "true",
            require_human_review=os.getenv("LEGAL_ADVERTISING_HUMAN_REVIEW", "false").lower() == "true"
        ),
        LegalDomain.PERSONAL_DATA: DomainConfig(
            enabled=os.getenv("LEGAL_PERSONAL_DATA_ENABLED", "true").lower() == "true",
            risk_threshold=float(os.getenv("LEGAL_PERSONAL_DATA_THRESHOLD", "0.8")),
            auto_disclaimer=os.getenv("LEGAL_PERSONAL_DATA_AUTO_DISCLAIMER", "true").lower() == "true",
            require_human_review=os.getenv("LEGAL_PERSONAL_DATA_HUMAN_REVIEW", "true").lower() == "true"
        ),
        LegalDomain.COPYRIGHT: DomainConfig(
            enabled=os.getenv("LEGAL_COPYRIGHT_ENABLED", "true").lower() == "true",
            risk_threshold=float(os.getenv("LEGAL_COPYRIGHT_THRESHOLD", "0.5")),
            auto_disclaimer=os.getenv("LEGAL_COPYRIGHT_AUTO_DISCLAIMER", "false").lower() == "true",
            require_human_review=os.getenv("LEGAL_COPYRIGHT_HUMAN_REVIEW", "false").lower() == "true"
        )
    }
    
    # Создаем конфигурации для правил
    rule_configs = {
        "fin_investment_advice": LegalRuleConfig(
            enabled=os.getenv("LEGAL_RULE_INVESTMENT_ADVICE", "true").lower() == "true",
            severity_multiplier=float(os.getenv("LEGAL_RULE_INVESTMENT_SEVERITY", "1.0")),
            custom_disclaimer=os.getenv("LEGAL_RULE_INVESTMENT_DISCLAIMER")
        ),
        "med_health_advice": LegalRuleConfig(
            enabled=os.getenv("LEGAL_RULE_HEALTH_ADVICE", "true").lower() == "true",
            severity_multiplier=float(os.getenv("LEGAL_RULE_HEALTH_SEVERITY", "1.2")),
            custom_disclaimer=os.getenv("LEGAL_RULE_HEALTH_DISCLAIMER")
        ),
        "adv_misleading": LegalRuleConfig(
            enabled=os.getenv("LEGAL_RULE_MISLEADING", "true").lower() == "true",
            severity_multiplier=float(os.getenv("LEGAL_RULE_MISLEADING_SEVERITY", "0.8"))
        )
    }
    
    return LegalAgentConfig(
        agent_name=os.getenv("LEGAL_AGENT_NAME", "Legal Guard Agent"),
        max_concurrent_tasks=int(os.getenv("LEGAL_MAX_CONCURRENT_TASKS", "2")),
        performance_score=float(os.getenv("LEGAL_PERFORMANCE_SCORE", "0.7")),
        
        enable_auto_disclaimers=os.getenv("LEGAL_AUTO_DISCLAIMERS", "true").lower() == "true",
        enable_human_review_requests=os.getenv("LEGAL_HUMAN_REVIEW", "true").lower() == "true",
        strict_mode=os.getenv("LEGAL_STRICT_MODE", "false").lower() == "true",
        
        risk_thresholds={
            'critical_threshold': float(os.getenv("LEGAL_CRITICAL_THRESHOLD", "0.9")),
            'high_threshold': float(os.getenv("LEGAL_HIGH_THRESHOLD", "0.7")),
            'medium_threshold': float(os.getenv("LEGAL_MEDIUM_THRESHOLD", "0.5")),
            'low_threshold': float(os.getenv("LEGAL_LOW_THRESHOLD", "0.3"))
        },
        
        domain_configs=domain_configs,
        rule_configs=rule_configs,
        
        cache=CacheConfig(
            enabled=os.getenv("LEGAL_CACHE_ENABLED", "true").lower() == "true",
            ttl_hours=int(os.getenv("LEGAL_CACHE_TTL_HOURS", "6")),
            max_size=int(os.getenv("LEGAL_CACHE_MAX_SIZE", "1000")),
            cleanup_interval_hours=int(os.getenv("LEGAL_CACHE_CLEANUP_HOURS", "24"))
        ),
        
        enable_statistics=os.getenv("LEGAL_STATISTICS", "true").lower() == "true",
        log_detailed_reports=os.getenv("LEGAL_DETAILED_LOGS", "false").lower() == "true",
        enable_legal_qa=os.getenv("LEGAL_QA_ENABLED", "true").lower() == "true"
    )


# Предустановленные конфигурации
STRICT_CONFIG = LegalAgentConfig(
    agent_name="Legal Guard Agent (Strict Mode)",
    strict_mode=True,
    risk_thresholds={
        'critical_threshold': 0.8,
        'high_threshold': 0.6,
        'medium_threshold': 0.4,
        'low_threshold': 0.2
    },
    enable_auto_disclaimers=True,
    enable_human_review_requests=True
)

PERMISSIVE_CONFIG = LegalAgentConfig(
    agent_name="Legal Guard Agent (Permissive Mode)",
    strict_mode=False,
    risk_thresholds={
        'critical_threshold': 0.95,
        'high_threshold': 0.8,
        'medium_threshold': 0.6,
        'low_threshold': 0.4
    },
    enable_auto_disclaimers=False,
    enable_human_review_requests=False
)

FINANCIAL_FOCUS_CONFIG = LegalAgentConfig(
    agent_name="Legal Guard Agent (Financial Focus)",
    domain_configs={
        LegalDomain.FINANCIAL: DomainConfig(
            enabled=True,
            risk_threshold=0.5,
            auto_disclaimer=True,
            require_human_review=True
        ),
        LegalDomain.MEDICAL: DomainConfig(
            enabled=False
        ),
        LegalDomain.ADVERTISING: DomainConfig(
            enabled=True,
            risk_threshold=0.7
        )
    }
)
