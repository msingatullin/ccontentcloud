"""
Пример использования Legal Guard Agent
Демонстрирует возможности юридической проверки контента
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from .legal_guard_agent import LegalGuardAgent, RiskLevel, LegalDomain
from .legal_config import load_config_from_env, STRICT_CONFIG, FINANCIAL_FOCUS_CONFIG


async def example_legal_check():
    """Пример юридической проверки контента"""
    
    # Создаем агента с конфигурацией по умолчанию
    legal_agent = LegalGuardAgent("legal_guard_001")
    
    # Примеры контента для проверки
    test_contents = [
        {
            "id": "financial_advice",
            "content": """
            Инвестируйте в акции компании XYZ! 
            Мы гарантируем 100% доходность в течение года.
            Это лучшая инвестиционная возможность на рынке.
            """,
            "type": "social_media_post"
        },
        {
            "id": "medical_advice", 
            "content": """
            При головной боли принимайте аспирин.
            Этот препарат поможет от всех видов боли.
            Рекомендуем покупать именно наш аспирин.
            """,
            "type": "blog_post"
        },
        {
            "id": "advertising_content",
            "content": """
            Наш продукт лучше всех конкурентов!
            Только у нас эксклюзивная технология.
            Покупайте сейчас со скидкой 50%!
            """,
            "type": "advertisement"
        },
        {
            "id": "personal_data",
            "content": """
            Мы собираем ваши персональные данные для улучшения сервиса.
            Ваша информация будет храниться в нашей базе данных.
            """,
            "type": "privacy_policy"
        },
        {
            "id": "copyright_issue",
            "content": """
            "Это очень длинная цитата из книги, которая может нарушать авторские права, 
            если она слишком большая и не имеет соответствующего оформления."
            """,
            "type": "article"
        },
        {
            "id": "safe_content",
            "content": """
            Сегодня хорошая погода. 
            Рекомендуем прогуляться в парке.
            Это полезно для здоровья.
            """,
            "type": "lifestyle_post"
        }
    ]
    
    print("🔍 LEGAL GUARD AGENT - ПРИМЕРЫ ПРОВЕРКИ КОНТЕНТА")
    print("=" * 60)
    
    for test_case in test_contents:
        print(f"\n📄 Проверка контента: {test_case['id']}")
        print(f"Тип: {test_case['type']}")
        print(f"Содержание: {test_case['content'].strip()}")
        print("-" * 40)
        
        # Создаем задачу для проверки
        from app.orchestrator.workflow_engine import Task, TaskType
        
        task = Task(
            name=f"legal_check_{test_case['id']}",
            task_type=TaskType.PLANNED,
            context={
                "content": test_case['content'],
                "content_id": test_case['id'],
                "content_type": test_case['type']
            }
        )
        
        try:
            # Выполняем проверку
            result = await legal_agent.execute_task(task)
            
            # Выводим результаты
            print(f"🎯 Общий уровень риска: {result['overall_risk_level'].upper()}")
            print(f"📊 Балл соответствия: {result['compliance_score']}/100")
            print(f"👤 Требуется проверка человека: {'Да' if result['requires_human_review'] else 'Нет'}")
            
            if result['risks']:
                print(f"⚠️  Найдено рисков: {len(result['risks'])}")
                for i, risk in enumerate(result['risks'], 1):
                    print(f"   {i}. {risk['level'].upper()}: {risk['description']}")
                    print(f"      Область: {risk['domain']}")
                    print(f"      Действие: {risk['suggested_action']}")
                    if risk['disclaimer_text']:
                        print(f"      Дисклеймер: {risk['disclaimer_text']}")
            else:
                print("✅ Рисков не обнаружено")
            
            if result['disclaimers_added']:
                print(f"📝 Добавлены дисклеймеры:")
                for disclaimer in result['disclaimers_added']:
                    print(f"   • {disclaimer}")
            
            if result['recommendations']:
                print(f"💡 Рекомендации:")
                for rec in result['recommendations']:
                    print(f"   • {rec}")
                    
        except Exception as e:
            print(f"❌ Ошибка при проверке: {e}")
        
        print()


async def example_legal_qa():
    """Пример юридической консультации"""
    
    legal_agent = LegalGuardAgent("legal_qa_001")
    
    questions = [
        "Можно ли рекламировать лекарства?",
        "Как обрабатывать персональные данные?",
        "Что нужно знать об авторских правах?",
        "Какие требования к финансовой рекламе?",
        "Как оформить медицинские советы?"
    ]
    
    print("\n🤖 LEGAL GUARD AGENT - ЮРИДИЧЕСКАЯ КОНСУЛЬТАЦИЯ")
    print("=" * 60)
    
    for question in questions:
        print(f"\n❓ Вопрос: {question}")
        
        try:
            answer = await legal_agent.get_legal_advice(question)
            print(f"💡 Ответ: {answer['answer']}")
            print(f"📊 Уверенность: {answer['confidence']}")
            print(f"📚 Источник: {answer['source']}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")


async def example_statistics():
    """Пример получения статистики"""
    
    legal_agent = LegalGuardAgent("legal_stats_001")
    
    print("\n📈 LEGAL GUARD AGENT - СТАТИСТИКА")
    print("=" * 60)
    
    try:
        stats = legal_agent.get_check_statistics()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")


async def example_different_configs():
    """Пример работы с разными конфигурациями"""
    
    print("\n⚙️ LEGAL GUARD AGENT - РАЗНЫЕ КОНФИГУРАЦИИ")
    print("=" * 60)
    
    configs = [
        ("Стандартная", load_config_from_env()),
        ("Строгая", STRICT_CONFIG),
        ("Финансовая фокус", FINANCIAL_FOCUS_CONFIG)
    ]
    
    test_content = "Инвестируйте в акции! Гарантируем доходность 100%!"
    
    for config_name, config in configs:
        print(f"\n🔧 Конфигурация: {config_name}")
        print(f"   Строгий режим: {config.strict_mode}")
        print(f"   Авто-дисклеймеры: {config.enable_auto_disclaimers}")
        print(f"   Человеческая проверка: {config.enable_human_review_requests}")
        
        # Здесь можно было бы создать агента с конкретной конфигурацией
        # Но для простоты примера просто показываем настройки
        print(f"   Пороги рисков: {config.risk_thresholds}")


async def main():
    """Главная функция с примерами"""
    
    print("🛡️ LEGAL GUARD AGENT - ДЕМОНСТРАЦИЯ ВОЗМОЖНОСТЕЙ")
    print("=" * 80)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Запускаем примеры
        await example_legal_check()
        await example_legal_qa()
        await example_statistics()
        await example_different_configs()
        
        print("\n✅ Все примеры выполнены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка выполнения примеров: {e}")


if __name__ == "__main__":
    # Запускаем примеры
    asyncio.run(main())
