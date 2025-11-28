#!/usr/bin/env python3
"""
Простой тест интеграции Vertex AI (Gemini + Grounding)
Запуск: python test_vertex_simple.py
"""

import asyncio
import os
import sys

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем переменные окружения если не заданы
if not os.getenv('GOOGLE_CLOUD_PROJECT'):
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'content-curator-1755119514'

if not os.getenv('GOOGLE_CLOUD_LOCATION'):
    os.environ['GOOGLE_CLOUD_LOCATION'] = 'us-central1'


async def test_gemini_with_grounding():
    """Тест Gemini с Google Search Grounding"""
    print("=" * 60)
    print("🧪 Тест Vertex AI: Gemini 1.5 Flash с Grounding")
    print("=" * 60)
    
    try:
        from app.mcp.integrations.vertex_ai import VertexAIIntegration
        
        # 1. Инициализация
        print("\n📦 Инициализация VertexAIIntegration...")
        vertex = VertexAIIntegration()
        print(f"   Project: {vertex.project_id}")
        print(f"   Location: {vertex.location}")
        print(f"   Model: {vertex.default_text_model}")
        
        # 2. Подключение
        print("\n🔌 Подключение к Vertex AI...")
        connect_result = await vertex.connect()
        if connect_result.success:
            print("   ✅ Подключено успешно")
        else:
            print(f"   ❌ Ошибка подключения: {connect_result.error}")
            return
        
        # 3. Health check
        print("\n🏥 Проверка здоровья...")
        health_result = await vertex.health_check()
        if health_result.success:
            print(f"   ✅ Сервис здоров: {health_result.data}")
        else:
            print(f"   ⚠️ Проблема: {health_result.error}")
        
        # 4. Запрос с Grounding
        question = "Кто президент Аргентины сейчас?"
        print(f"\n🔍 Вопрос: {question}")
        print("   (с Google Search Grounding)")
        print("-" * 40)
        
        response = await vertex.generate_text(
            prompt=question,
            use_grounding=True,  # Включаем Google Search
            temperature=0.3,    # Низкая температура для точности
            max_output_tokens=500
        )
        
        if response.success:
            print("\n📝 Ответ Gemini:")
            print("-" * 40)
            print(response.data.get('generated_text', 'Нет текста'))
            print("-" * 40)
            print(f"\n📊 Метаданные:")
            for key, value in response.metadata.items():
                print(f"   {key}: {value}")
        else:
            print(f"\n❌ Ошибка: {response.error}")
        
        # 5. Тест без Grounding для сравнения
        print("\n" + "=" * 60)
        print("🔄 Тот же вопрос БЕЗ Grounding (для сравнения):")
        print("-" * 40)
        
        response_no_grounding = await vertex.generate_text(
            prompt=question,
            use_grounding=False,
            temperature=0.3,
            max_output_tokens=500
        )
        
        if response_no_grounding.success:
            print(response_no_grounding.data.get('generated_text', 'Нет текста'))
        else:
            print(f"❌ Ошибка: {response_no_grounding.error}")
        
        print("\n" + "=" * 60)
        print("✅ Тест завершён")
        print("=" * 60)
        
    except ImportError as e:
        print(f"\n❌ Ошибка импорта: {e}")
        print("   Убедитесь что установлен google-cloud-aiplatform:")
        print("   pip install google-cloud-aiplatform>=1.38.0")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def test_fact_check():
    """Тест метода fact_check"""
    print("\n" + "=" * 60)
    print("🔬 Тест Fact Check")
    print("=" * 60)
    
    try:
        from app.mcp.integrations.vertex_ai import VertexAIIntegration
        
        vertex = VertexAIIntegration()
        await vertex.connect()
        
        claim = "Эйфелева башня была построена в 1889 году"
        print(f"\n📋 Проверяем утверждение: {claim}")
        print("-" * 40)
        
        result = await vertex.fact_check(claim)
        
        if result.success:
            print("\n📝 Результат фактчека:")
            print(result.data.get('generated_text', 'Нет ответа'))
        else:
            print(f"❌ Ошибка: {result.error}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def test_image_generation():
    """Тест генерации изображений через Gemini"""
    print("\n" + "=" * 60)
    print("🎨 Тест генерации изображений (gemini-2.5-flash-image)")
    print("=" * 60)
    
    try:
        from app.mcp.integrations.vertex_ai import VertexAIIntegration
        
        vertex = VertexAIIntegration()
        await vertex.connect()
        
        prompt = "A beautiful sunset over mountains with a lake reflection"
        print(f"\n🖼️ Промпт: {prompt}")
        print("-" * 40)
        
        result = await vertex.generate_image(prompt)
        
        if result.success:
            print("\n✅ Изображение сгенерировано!")
            images = result.data.get('images', [])
            for img in images:
                print(f"   📁 Файл: {img.get('file_path')}")
                print(f"   📏 Размер: {img.get('bytes_length')} bytes")
                print(f"   🎨 Формат: {img.get('format')}")
            print(f"\n📊 Метаданные: {result.metadata}")
        else:
            print(f"❌ Ошибка: {result.error}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Запуск тестов Vertex AI\n")
    
    # Запускаем основной тест
    asyncio.run(test_gemini_with_grounding())
    
    # Тест генерации изображений
    asyncio.run(test_image_generation())
    
    # Опционально: тест фактчека
    # asyncio.run(test_fact_check())

