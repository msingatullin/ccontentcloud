"""
Модели для источников контента и мониторинга веб-сайтов
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from app.database.connection import Base
from datetime import datetime


class ContentSource(Base):
    """Источники контента для мониторинга"""
    __tablename__ = 'content_sources'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Основная информация
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Тип источника и URL
    source_type = Column(String(50), nullable=False, index=True)  # 'website', 'rss', 'news_api', 'social'
    url = Column(Text, nullable=False)
    
    # Конфигурация источника
    config = Column(JSON, default=dict)  # Селекторы, параметры API и т.д.
    
    # Метод извлечения контента
    extraction_method = Column(String(50), default='ai')  # 'ai', 'selectors', 'rss'
    
    # Правила фильтрации
    keywords = Column(JSON, default=list)  # Ключевые слова для поиска
    exclude_keywords = Column(JSON, default=list)  # Исключающие слова
    categories = Column(JSON, default=list)  # Категории контента
    
    # Настройки автопостинга
    auto_post_enabled = Column(Boolean, default=True, nullable=False)
    post_delay_minutes = Column(Integer, default=0)  # Задержка перед публикацией
    post_template = Column(Text, nullable=True)  # Шаблон поста: "{title}\n\n{description}\n\n{url}"
    
    # Связь с правилами автопостинга
    auto_posting_rule_id = Column(Integer, ForeignKey('auto_posting_rules.id', ondelete='SET NULL'), nullable=True)
    
    # Расписание проверок
    check_interval_minutes = Column(Integer, default=60, nullable=False)  # Интервал проверки
    next_check_at = Column(DateTime, nullable=True, index=True)
    last_check_at = Column(DateTime, nullable=True)
    last_check_status = Column(String(50), nullable=True)  # 'success', 'error'
    last_error_message = Column(Text, nullable=True)
    
    # Статус источника
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Статистика
    total_checks = Column(Integer, default=0, nullable=False)
    total_items_found = Column(Integer, default=0, nullable=False)
    total_items_new = Column(Integer, default=0, nullable=False)
    total_posts_created = Column(Integer, default=0, nullable=False)
    
    # Хранение последнего снимка для diff
    last_snapshot_hash = Column(String(64), nullable=True)  # MD5 хеш контента
    last_snapshot_data = Column(JSON, nullable=True)  # Структурированные данные
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связи
    user = relationship("User", back_populates="content_sources")
    auto_posting_rule = relationship("AutoPostingRuleDB", foreign_keys=[auto_posting_rule_id])
    monitored_items = relationship("MonitoredItem", back_populates="source", cascade="all, delete-orphan")
    check_history = relationship("SourceCheckHistory", back_populates="source", cascade="all, delete-orphan")
    
    # Индексы
    __table_args__ = (
        Index('ix_content_sources_user_active', 'user_id', 'is_active'),
        Index('ix_content_sources_next_check', 'next_check_at', 'is_active'),
        Index('ix_content_sources_type', 'source_type', 'is_active'),
    )
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'source_type': self.source_type,
            'url': self.url,
            'config': self.config or {},
            'extraction_method': self.extraction_method,
            'keywords': self.keywords or [],
            'exclude_keywords': self.exclude_keywords or [],
            'categories': self.categories or [],
            'auto_post_enabled': self.auto_post_enabled,
            'post_delay_minutes': self.post_delay_minutes,
            'post_template': self.post_template,
            'auto_posting_rule_id': self.auto_posting_rule_id,
            'check_interval_minutes': self.check_interval_minutes,
            'next_check_at': self.next_check_at.isoformat() if self.next_check_at else None,
            'last_check_at': self.last_check_at.isoformat() if self.last_check_at else None,
            'last_check_status': self.last_check_status,
            'last_error_message': self.last_error_message,
            'is_active': self.is_active,
            'total_checks': self.total_checks,
            'total_items_found': self.total_items_found,
            'total_items_new': self.total_items_new,
            'total_posts_created': self.total_posts_created,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<ContentSource(id={self.id}, name='{self.name}', type='{self.source_type}', active={self.is_active})>"


class MonitoredItem(Base):
    """Найденные элементы контента из источников"""
    __tablename__ = 'monitored_items'
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('content_sources.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Данные элемента
    external_id = Column(String(255), nullable=True, index=True)  # ID из RSS, URL страницы
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime, nullable=True, index=True)
    
    # Метаданные
    raw_data = Column(JSON, nullable=True)  # Полные данные из источника
    extracted_data = Column(JSON, nullable=True)  # Обработанные данные
    
    # Обработка и статус
    status = Column(String(50), default='new', nullable=False, index=True)  # new, approved, posted, ignored, duplicate, error
    duplicate_of = Column(Integer, ForeignKey('monitored_items.id', ondelete='SET NULL'), nullable=True)
    
    # AI анализ
    relevance_score = Column(Float, default=0.0, nullable=False)  # 0.0-1.0
    ai_summary = Column(Text, nullable=True)
    ai_sentiment = Column(String(50), nullable=True)  # positive, negative, neutral
    ai_category = Column(String(100), nullable=True)
    ai_keywords = Column(JSON, default=list)
    
    # Связь с созданным контентом
    content_id = Column(String(36), ForeignKey('content_pieces.id', ondelete='SET NULL'), nullable=True)
    scheduled_post_id = Column(Integer, ForeignKey('scheduled_posts.id', ondelete='SET NULL'), nullable=True)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    
    # Связи
    source = relationship("ContentSource", back_populates="monitored_items")
    user = relationship("User", back_populates="monitored_items")
    content = relationship("ContentPieceDB", foreign_keys=[content_id])
    scheduled_post = relationship("ScheduledPostDB", foreign_keys=[scheduled_post_id])
    
    # Индексы
    __table_args__ = (
        Index('ix_monitored_items_source_status', 'source_id', 'status'),
        Index('ix_monitored_items_user_status', 'user_id', 'status'),
        Index('ix_monitored_items_published', 'published_at', 'status'),
        Index('ix_monitored_items_relevance', 'relevance_score', 'status'),
    )
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'source_id': self.source_id,
            'user_id': self.user_id,
            'external_id': self.external_id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'url': self.url,
            'image_url': self.image_url,
            'author': self.author,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'status': self.status,
            'duplicate_of': self.duplicate_of,
            'relevance_score': self.relevance_score,
            'ai_summary': self.ai_summary,
            'ai_sentiment': self.ai_sentiment,
            'ai_category': self.ai_category,
            'ai_keywords': self.ai_keywords or [],
            'content_id': self.content_id,
            'scheduled_post_id': self.scheduled_post_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'posted_at': self.posted_at.isoformat() if self.posted_at else None
        }
    
    def __repr__(self):
        return f"<MonitoredItem(id={self.id}, title='{self.title[:30]}...', status='{self.status}')>"


class SourceCheckHistory(Base):
    """История проверок источников"""
    __tablename__ = 'source_check_history'
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('content_sources.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Результаты проверки
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    items_found = Column(Integer, default=0, nullable=False)
    items_new = Column(Integer, default=0, nullable=False)
    items_duplicate = Column(Integer, default=0, nullable=False)
    items_posted = Column(Integer, default=0, nullable=False)
    
    # Статус
    status = Column(String(50), nullable=False)  # 'success', 'error', 'partial'
    error_message = Column(Text, nullable=True)
    
    # Производительность
    execution_time_ms = Column(Integer, nullable=True)
    
    # Связи
    source = relationship("ContentSource", back_populates="check_history")
    
    # Индексы
    __table_args__ = (
        Index('ix_source_check_history_source_date', 'source_id', 'checked_at'),
    )
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'source_id': self.source_id,
            'checked_at': self.checked_at.isoformat() if self.checked_at else None,
            'items_found': self.items_found,
            'items_new': self.items_new,
            'items_duplicate': self.items_duplicate,
            'items_posted': self.items_posted,
            'status': self.status,
            'error_message': self.error_message,
            'execution_time_ms': self.execution_time_ms
        }
    
    def __repr__(self):
        return f"<SourceCheckHistory(id={self.id}, source_id={self.source_id}, status='{self.status}')>"

