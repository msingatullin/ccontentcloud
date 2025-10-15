"""
Модели данных для загруженных файлов
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.orm import relationship

from ..database.connection import Base


class FileUploadDB(Base):
    """Модель для хранения информации о загруженных файлах"""
    __tablename__ = 'file_uploads'
    
    # Идентификаторы
    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Информация о файле
    filename = Column(String, nullable=False)  # Сгенерированное имя
    original_filename = Column(String, nullable=False)  # Оригинальное имя
    file_type = Column(String, nullable=False, index=True)  # image, video, document
    mime_type = Column(String, nullable=False)  # image/jpeg, application/pdf, etc.
    size_bytes = Column(BigInteger, nullable=False)  # Размер в байтах
    
    # Хранилище GCS
    storage_url = Column(String, nullable=False)  # Публичный URL
    storage_bucket = Column(String, nullable=False)  # Имя bucket
    storage_path = Column(String, nullable=False)  # Путь в bucket
    
    # AI анализ (для изображений)
    ai_description = Column(Text)  # Описание от Vision API
    ai_metadata = Column(JSON, default=dict)  # Дополнительные данные от AI
    
    # Парсинг документов
    extracted_text = Column(Text)  # Извлеченный текст из документа
    document_metadata = Column(JSON, default=dict)  # Метаданные документа
    
    # Использование
    used_in_content = Column(JSON, default=list)  # IDs контента где использован
    usage_count = Column(Integer, default=0)  # Сколько раз использован
    
    # Статус и флаги
    is_processed = Column(Boolean, default=False)  # Обработан ли AI/парсером
    is_public = Column(Boolean, default=True)  # Публичный доступ
    is_deleted = Column(Boolean, default=False)  # Мягкое удаление
    
    # Даты
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    processed_at = Column(DateTime)  # Когда обработан AI
    last_accessed_at = Column(DateTime)  # Последний доступ
    deleted_at = Column(DateTime)  # Дата удаления
    
    # Связи
    user = relationship("User", back_populates="uploads")
    
    def __repr__(self):
        return f"<FileUpload {self.id}: {self.original_filename} ({self.file_type})>"
    
    def to_dict(self):
        """Преобразует модель в словарь"""
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "size_kb": round(self.size_bytes / 1024, 2),
            "size_mb": round(self.size_bytes / (1024 * 1024), 2),
            "url": self.storage_url,
            "ai_description": self.ai_description,
            "ai_metadata": self.ai_metadata,
            "extracted_text_preview": self.extracted_text[:200] if self.extracted_text else None,
            "document_metadata": self.document_metadata,
            "used_in_content": self.used_in_content,
            "usage_count": self.usage_count,
            "is_processed": self.is_processed,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None
        }
    
    def to_dict_full(self):
        """Полная информация включая весь текст"""
        data = self.to_dict()
        data['extracted_text'] = self.extracted_text
        return data

