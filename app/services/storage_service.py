"""
Сервис для работы с Google Cloud Storage
Загрузка, хранение и управление медиа-файлами
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, BinaryIO
from pathlib import Path
import mimetypes
import logging

from google.cloud import storage
from werkzeug.utils import secure_filename
from PIL import Image
import io

logger = logging.getLogger(__name__)


class StorageService:
    """Сервис для работы с Google Cloud Storage"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.bucket_name = os.getenv('GCS_BUCKET_NAME', 'content-curator-uploads')
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'content-curator-1755119514')
        
        # Инициализируем клиент GCS
        try:
            self.client = storage.Client(project=self.project_id)
            self.bucket = self.client.bucket(self.bucket_name)
            logger.info(f"Storage service initialized with bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            self.client = None
            self.bucket = None
    
    def _generate_file_path(self, user_id: str, filename: str, folder: str = "uploads") -> str:
        """
        Генерирует путь для файла в bucket
        Формат: /{user_id}/{folder}/{year}/{month}/{uuid}-{filename}
        """
        now = datetime.utcnow()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        
        # Генерируем уникальное имя
        file_uuid = str(uuid.uuid4())[:8]
        safe_filename = secure_filename(filename)
        
        return f"{user_id}/{folder}/{year}/{month}/{file_uuid}-{safe_filename}"
    
    def _get_content_type(self, filename: str) -> str:
        """Определяет MIME type файла"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    def _optimize_image(self, file_content: bytes, max_size: int = 2048) -> bytes:
        """
        Оптимизирует изображение
        - Уменьшает размер если больше max_size
        - Конвертирует в WebP для веба
        """
        try:
            img = Image.open(io.BytesIO(file_content))
            
            # Проверяем размер
            if max(img.size) > max_size:
                # Пропорциональное уменьшение
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Конвертируем в RGB если RGBA
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            
            # Сохраняем оптимизированное изображение
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to optimize image: {e}")
            return file_content
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        folder: str = "uploads",
        optimize: bool = True
    ) -> Dict[str, Any]:
        """
        Загружает файл в GCS
        
        Args:
            file_content: Содержимое файла в байтах
            filename: Оригинальное имя файла
            user_id: ID пользователя
            folder: Папка для хранения (images, documents, videos)
            optimize: Оптимизировать изображения
        
        Returns:
            Dict с информацией о загруженном файле
        """
        try:
            if not self.bucket:
                raise Exception("GCS bucket not initialized")
            
            # Определяем тип файла
            content_type = self._get_content_type(filename)
            
            # Оптимизируем изображения
            if optimize and content_type.startswith('image/'):
                file_content = self._optimize_image(file_content)
                filename = Path(filename).stem + '.jpg'  # Меняем расширение на jpg
                content_type = 'image/jpeg'
            
            # Генерируем путь
            file_path = self._generate_file_path(user_id, filename, folder)
            
            # Создаем blob
            blob = self.bucket.blob(file_path)
            
            # Загружаем файл
            blob.upload_from_string(
                file_content,
                content_type=content_type
            )
            
            file_url = f"https://storage.googleapis.com/{self.bucket_name}/{file_path}"
            is_public = True

            try:
                blob.make_public()
                logger.info(f"File made public: {file_path}")
            except Exception as public_error:
                is_public = False
                logger.warning(f"Failed to make file public (will use signed URL): {public_error}")
                try:
                    expiration_hours = int(os.getenv('GCS_SIGNED_URL_EXPIRATION_HOURS', '24'))
                except ValueError:
                    expiration_hours = 24
                file_url = blob.generate_signed_url(expiration=timedelta(hours=expiration_hours))

            logger.info(f"File uploaded successfully: {file_path}")
            
            return {
                "success": True,
                "url": file_url,
                "path": file_path,
                "filename": filename,
                "original_filename": filename,
                "size_bytes": len(file_content),
                "content_type": content_type,
                "bucket": self.bucket_name,
                "is_public": is_public
            }
            
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Удаляет файл из GCS
        
        Args:
            file_path: Путь к файлу в bucket
        
        Returns:
            True если успешно удален
        """
        try:
            if not self.bucket:
                raise Exception("GCS bucket not initialized")
            
            blob = self.bucket.blob(file_path)
            blob.delete()
            
            logger.info(f"File deleted successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о файле
        
        Args:
            file_path: Путь к файлу в bucket
        
        Returns:
            Dict с информацией о файле или None
        """
        try:
            if not self.bucket:
                raise Exception("GCS bucket not initialized")
            
            blob = self.bucket.blob(file_path)
            
            if not blob.exists():
                return None
            
            blob.reload()
            
            return {
                "name": blob.name,
                "size_bytes": blob.size,
                "content_type": blob.content_type,
                "created_at": blob.time_created,
                "updated_at": blob.updated,
                "url": blob.public_url
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return None
    
    async def list_user_files(
        self,
        user_id: str,
        folder: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        Получает список файлов пользователя
        
        Args:
            user_id: ID пользователя
            folder: Фильтр по папке
            limit: Максимальное количество файлов
        
        Returns:
            Список файлов
        """
        try:
            if not self.bucket:
                raise Exception("GCS bucket not initialized")
            
            # Формируем prefix для поиска
            prefix = f"{user_id}/"
            if folder:
                prefix = f"{user_id}/{folder}/"
            
            # Получаем список blobs
            blobs = self.client.list_blobs(
                self.bucket_name,
                prefix=prefix,
                max_results=limit
            )
            
            files = []
            for blob in blobs:
                files.append({
                    "name": blob.name,
                    "url": blob.public_url,
                    "size_bytes": blob.size,
                    "content_type": blob.content_type,
                    "created_at": blob.time_created.isoformat() if blob.time_created else None
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    def get_signed_url(self, file_path: str, expiration: int = 3600) -> Optional[str]:
        """
        Генерирует подписанный URL для приватного файла
        
        Args:
            file_path: Путь к файлу
            expiration: Время жизни URL в секундах
        
        Returns:
            Подписанный URL или None
        """
        try:
            if not self.bucket:
                raise Exception("GCS bucket not initialized")
            
            blob = self.bucket.blob(file_path)
            url = blob.generate_signed_url(expiration=expiration)
            
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            return None


# Singleton instance
_storage_service = None


def get_storage_service() -> StorageService:
    """Получить singleton instance Storage Service"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service

