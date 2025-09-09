"""
Пример использования Multimedia Producer Agent
Демонстрирует основные возможности агента для создания визуального контента
"""

import asyncio
from datetime import datetime
from app.agents.multimedia_producer_agent import (
    MultimediaProducerAgent,
    ImageGenerationRequest,
    ContentType,
    ImageFormat
)
from app.models.workflow import Task, TaskType, TaskPriority


async def example_image_generation():
    """Пример генерации изображения"""
    print("🎨 Пример генерации изображения")
    
    # Создаем агента
    agent = MultimediaProducerAgent()
    
    # Создаем задачу для генерации изображения
    task_data = {
        "prompt": "Modern office workspace with laptop, coffee cup, and plants, professional lighting",
        "content_type": "image",
        "format": "square",
        "style": "professional"
    }
    
    task = Task(
        task_id="img_gen_001",
        task_type=TaskType.PLANNED,
        priority=TaskPriority.MEDIUM,
        data=task_data,
        created_at=datetime.now()
    )
    
    # Выполняем задачу
    result = await agent.execute_task(task)
    
    if result["success"]:
        generated_image = result["result"]
        print(f"✅ Изображение сгенерировано:")
        print(f"   ID: {generated_image.image_id}")
        print(f"   Путь: {generated_image.image_path}")
        print(f"   Размер: {generated_image.dimensions}")
        print(f"   Время генерации: {generated_image.generation_time:.2f}с")
    else:
        print(f"❌ Ошибка генерации: {result['error']}")


async def example_infographic_creation():
    """Пример создания инфографики"""
    print("\n📊 Пример создания инфографики")
    
    agent = MultimediaProducerAgent()
    
    # Данные для инфографики
    infographic_data = {
        "title": "Статистика использования AI в 2024",
        "stat1": "85%",
        "stat2": "2.3M",
        "description": "Компаний используют AI технологии для автоматизации процессов"
    }
    
    task_data = {
        "content_type": "infographic",
        "template_id": "stats_template",
        "format": "square",
        "data": infographic_data
    }
    
    task = Task(
        task_id="infographic_001",
        task_type=TaskType.COMPLEX,
        priority=TaskPriority.HIGH,
        data=task_data,
        created_at=datetime.now()
    )
    
    result = await agent.execute_task(task)
    
    if result["success"]:
        infographic = result["result"]
        print(f"✅ Инфографика создана:")
        print(f"   ID: {infographic.image_id}")
        print(f"   Путь: {infographic.image_path}")
        print(f"   Размер файла: {infographic.file_size} байт")
    else:
        print(f"❌ Ошибка создания инфографики: {result['error']}")


async def example_carousel_post():
    """Пример создания карусельного поста"""
    print("\n🎠 Пример создания карусельного поста")
    
    agent = MultimediaProducerAgent()
    
    # Слайды для карусели
    slides_data = [
        {
            "prompt": "Slide 1: Title slide with 'AI Trends 2024' text, modern design",
            "format": "square"
        },
        {
            "prompt": "Slide 2: Statistics about AI adoption, clean infographic style",
            "format": "square"
        },
        {
            "prompt": "Slide 3: Call to action with 'Learn More' button, professional",
            "format": "square"
        }
    ]
    
    task_data = {
        "content_type": "carousel_post",
        "format": "square",
        "slides": slides_data
    }
    
    task = Task(
        task_id="carousel_001",
        task_type=TaskType.COMPLEX,
        priority=TaskPriority.MEDIUM,
        data=task_data,
        created_at=datetime.now()
    )
    
    result = await agent.execute_task(task)
    
    if result["success"]:
        carousel_slides = result["result"]
        print(f"✅ Карусельный пост создан:")
        print(f"   Количество слайдов: {len(carousel_slides)}")
        for i, slide in enumerate(carousel_slides, 1):
            print(f"   Слайд {i}: {slide.image_path}")
    else:
        print(f"❌ Ошибка создания карусели: {result['error']}")


async def example_video_cover():
    """Пример создания обложки для видео"""
    print("\n🎬 Пример создания обложки для видео")
    
    agent = MultimediaProducerAgent()
    
    task_data = {
        "content_type": "video_cover",
        "format": "horizontal",
        "title": "Как AI изменит маркетинг в 2024",
        "description": "Эксклюзивное интервью с экспертами"
    }
    
    task = Task(
        task_id="video_cover_001",
        task_type=TaskType.PLANNED,
        priority=TaskPriority.HIGH,
        data=task_data,
        created_at=datetime.now()
    )
    
    result = await agent.execute_task(task)
    
    if result["success"]:
        video_cover = result["result"]
        print(f"✅ Обложка видео создана:")
        print(f"   ID: {video_cover.image_id}")
        print(f"   Путь: {video_cover.image_path}")
        print(f"   Размер: {video_cover.dimensions}")
    else:
        print(f"❌ Ошибка создания обложки: {result['error']}")


async def example_batch_generation():
    """Пример пакетной генерации изображений"""
    print("\n⚡ Пример пакетной генерации")
    
    agent = MultimediaProducerAgent()
    
    # Создаем несколько запросов
    requests = [
        ImageGenerationRequest(
            prompt="Professional headshot, business attire, studio lighting",
            content_type=ContentType.IMAGE,
            image_format=ImageFormat.SQUARE,
            style="professional"
        ),
        ImageGenerationRequest(
            prompt="Modern product photo, white background, clean lighting",
            content_type=ContentType.IMAGE,
            image_format=ImageFormat.SQUARE,
            style="commercial"
        ),
        ImageGenerationRequest(
            prompt="Team meeting, diverse professionals, modern office",
            content_type=ContentType.IMAGE,
            image_format=ImageFormat.HORIZONTAL,
            style="corporate"
        )
    ]
    
    # Генерируем пакетно
    results = await agent.create_image_batch(requests)
    
    print(f"✅ Пакетная генерация завершена:")
    print(f"   Запрошено: {len(requests)} изображений")
    print(f"   Создано: {len(results)} изображений")
    
    for i, result in enumerate(results, 1):
        print(f"   Изображение {i}: {result.image_path}")


async def example_stock_search():
    """Пример поиска стоковых изображений"""
    print("\n🔍 Пример поиска стоковых изображений")
    
    agent = MultimediaProducerAgent()
    
    # Ищем стоковые изображения
    stock_images = await agent.search_stock_images("business meeting", count=5)
    
    if stock_images:
        print(f"✅ Найдено {len(stock_images)} стоковых изображений:")
        for i, image in enumerate(stock_images, 1):
            print(f"   {i}. {image.get('alt_description', 'No description')}")
            print(f"      URL: {image.get('urls', {}).get('small', 'N/A')}")
    else:
        print("❌ Стоковые изображения не найдены")


async def example_optimization():
    """Пример оптимизации изображений"""
    print("\n⚙️ Пример оптимизации изображений")
    
    agent = MultimediaProducerAgent()
    
    # Создаем тестовое изображение
    task_data = {
        "prompt": "Test image for optimization",
        "content_type": "image",
        "format": "square"
    }
    
    task = Task(
        task_id="opt_test_001",
        task_type=TaskType.PLANNED,
        priority=TaskPriority.LOW,
        data=task_data,
        created_at=datetime.now()
    )
    
    result = await agent.execute_task(task)
    
    if result["success"]:
        original_image = result["result"]
        print(f"✅ Исходное изображение создано: {original_image.image_path}")
        
        # Оптимизируем для разных платформ
        platforms = ["web", "social", "print"]
        
        for platform in platforms:
            optimized_path = await agent.optimize_image_for_platform(
                original_image.image_path, platform
            )
            print(f"   Оптимизировано для {platform}: {optimized_path}")
    else:
        print(f"❌ Ошибка создания тестового изображения: {result['error']}")


async def example_templates_info():
    """Пример получения информации о шаблонах"""
    print("\n📋 Доступные шаблоны инфографики")
    
    agent = MultimediaProducerAgent()
    
    templates = agent.get_available_templates()
    platform_formats = agent.get_platform_formats()
    
    print("✅ Шаблоны инфографики:")
    for template in templates:
        print(f"   - {template['name']} ({template['template_id']})")
        print(f"     Описание: {template['description']}")
        print(f"     Формат: {template['format']}")
        print(f"     Тип: {template['layout_type']}")
    
    print("\n✅ Форматы для платформ:")
    for platform, format_type in platform_formats.items():
        print(f"   - {platform}: {format_type}")


async def main():
    """Главная функция с примерами"""
    print("🚀 Multimedia Producer Agent - Примеры использования\n")
    
    try:
        # Запускаем примеры
        await example_image_generation()
        await example_infographic_creation()
        await example_carousel_post()
        await example_video_cover()
        await example_batch_generation()
        await example_stock_search()
        await example_optimization()
        await example_templates_info()
        
        print("\n✅ Все примеры выполнены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка выполнения примеров: {e}")


if __name__ == "__main__":
    asyncio.run(main())
