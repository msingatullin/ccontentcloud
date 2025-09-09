"""
Пример использования Community Concierge Agent
Демонстрирует возможности модерации комментариев и управления сообществом
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from .community_concierge_agent import CommunityConciergeAgent, CommentType, SentimentType, ResponseType, EscalationLevel
from .community_config import load_config_from_env, STRICT_MODERATION_CONFIG, FRIENDLY_MODERATION_CONFIG, AUTOMATED_CONFIG, HUMAN_FOCUSED_CONFIG


async def example_comment_moderation():
    """Пример модерации комментариев"""
    
    # Создаем агента с конфигурацией по умолчанию
    community_agent = CommunityConciergeAgent("community_001")
    
    # Примеры комментариев для модерации
    test_comments = [
        {
            "id": "comment_001",
            "user_id": "user_123",
            "username": "Алексей_Петров",
            "content": "Отличный пост! Очень полезная информация, спасибо!",
            "platform": "telegram",
            "post_id": "post_456",
            "timestamp": datetime.now().isoformat()
        },
        {
            "id": "comment_002",
            "user_id": "user_456",
            "username": "Мария_Иванова",
            "content": "Как зарегистрироваться в системе? Не могу найти кнопку регистрации",
            "platform": "telegram",
            "post_id": "post_456",
            "timestamp": datetime.now().isoformat()
        },
        {
            "id": "comment_003",
            "user_id": "user_789",
            "username": "Дмитрий_Сидоров",
            "content": "Ужасный сервис! Не работает уже третий день, деньги потрачены зря!",
            "platform": "telegram",
            "post_id": "post_456",
            "timestamp": datetime.now().isoformat()
        },
        {
            "id": "comment_004",
            "user_id": "user_101",
            "username": "Спам_Бот",
            "content": "КУПИТЕ КРИПТОВАЛЮТУ! ЗАРАБОТОК 1000% В ДЕНЬ! ПЕРЕХОДИТЕ ПО ССЫЛКЕ!",
            "platform": "telegram",
            "post_id": "post_456",
            "timestamp": datetime.now().isoformat()
        },
        {
            "id": "comment_005",
            "user_id": "user_202",
            "username": "Анна_Козлова",
            "content": "Подскажите, как настроить интеграцию с CRM? У нас Salesforce",
            "platform": "telegram",
            "post_id": "post_456",
            "timestamp": datetime.now().isoformat()
        },
        {
            "id": "comment_006",
            "user_id": "user_303",
            "username": "Игорь_Новиков",
            "content": "Нормально работает, но есть небольшие баги. В целом доволен",
            "platform": "telegram",
            "post_id": "post_456",
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    print("🛡️ COMMUNITY CONCIERGE AGENT - ПРИМЕРЫ МОДЕРАЦИИ КОММЕНТАРИЕВ")
    print("=" * 70)
    
    for test_comment in test_comments:
        print(f"\n💬 Комментарий: {test_comment['id']}")
        print(f"Пользователь: {test_comment['username']}")
        print(f"Содержание: {test_comment['content']}")
        print("-" * 50)
        
        # Создаем задачу для модерации
        from app.orchestrator.workflow_engine import Task, TaskType
        
        task = Task(
            name=f"moderate_{test_comment['id']}",
            task_type=TaskType.REAL_TIME,
            context={
                "comment": test_comment,
                "moderation_type": "auto"
            }
        )
        
        try:
            # Выполняем модерацию
            result = await community_agent.execute_task(task)
            
            # Выводим результаты
            moderation = result['moderation_result']
            analysis = result['analysis']
            
            print(f"🎯 Действие: {moderation['action']}")
            print(f"📊 Уверенность: {moderation['confidence']:.1%}")
            print(f"📝 Причина: {moderation['reason']}")
            
            if moderation['auto_reply']:
                print(f"🤖 Автоответ: {moderation['auto_reply']}")
            
            if moderation['escalation_level'] != 'none':
                print(f"⚠️ Эскалация: {moderation['escalation_level']}")
            
            if moderation['requires_human_review']:
                print("👤 Требуется проверка человеком")
            
            print(f"📈 Тип комментария: {analysis['comment_type']}")
            print(f"😊 Тональность: {analysis['sentiment']}")
            print(f"🌐 Язык: {analysis['language']}")
            
            if result['insights']:
                print(f"💡 Инсайты: {len(result['insights'])}")
                for insight in result['insights']:
                    print(f"   - {insight['title']}: {insight['description']}")
            
            print(f"⏱️ Время обработки: {result['processing_time']:.2f} сек")
                    
        except Exception as e:
            print(f"❌ Ошибка при модерации: {e}")
        
        print()


async def example_different_configurations():
    """Пример работы с разными конфигурациями"""
    
    print("\n⚙️ COMMUNITY CONCIERGE AGENT - РАЗНЫЕ КОНФИГУРАЦИИ")
    print("=" * 70)
    
    configs = [
        ("Стандартная", load_config_from_env()),
        ("Строгая модерация", STRICT_MODERATION_CONFIG),
        ("Дружелюбная модерация", FRIENDLY_MODERATION_CONFIG),
        ("Автоматизированная", AUTOMATED_CONFIG),
        ("С фокусом на человека", HUMAN_FOCUSED_CONFIG)
    ]
    
    for config_name, config in configs:
        print(f"\n🔧 Конфигурация: {config_name}")
        print(f"   Агент: {config.agent_name}")
        print(f"   Максимум задач: {config.max_concurrent_tasks}")
        print(f"   Производительность: {config.performance_score}")
        print(f"   Модерация: {config.moderation.enabled}")
        print(f"   Автоответы: {config.auto_reply.enabled}")
        print(f"   Эскалация: {config.escalation.enabled}")
        print(f"   Анализ тональности: {config.sentiment.enabled}")
        print(f"   Инсайты: {config.insights.enabled}")


async def example_sentiment_analysis():
    """Пример анализа тональности"""
    
    community_agent = CommunityConciergeAgent("community_sentiment_001")
    
    sentiment_test_cases = [
        "Отличный сервис! Очень доволен!",
        "Ужасный продукт, не рекомендую",
        "Нормально работает, есть небольшие баги",
        "СПАСИБО ЗА ПОМОЩЬ! ВЫ ЛУЧШИЕ!",
        "Плохо работает, но в целом приемлемо",
        "Как настроить интеграцию?",
        "КУПИТЕ КРИПТОВАЛЮТУ! ЗАРАБОТОК 1000%!"
    ]
    
    print("\n😊 COMMUNITY CONCIERGE AGENT - АНАЛИЗ ТОНАЛЬНОСТИ")
    print("=" * 70)
    
    for i, content in enumerate(sentiment_test_cases, 1):
        print(f"\n📝 Тест {i}: {content}")
        print("-" * 40)
        
        # Анализируем тональность
        sentiment = community_agent._analyze_sentiment(content)
        comment_type = community_agent._classify_comment_type(content)
        is_spam = community_agent._detect_spam(content)
        is_inappropriate = community_agent._detect_inappropriate(content)
        
        print(f"😊 Тональность: {sentiment.value}")
        print(f"📋 Тип: {comment_type.value}")
        print(f"🚫 Спам: {'Да' if is_spam else 'Нет'}")
        print(f"⚠️ Неподходящий: {'Да' if is_inappropriate else 'Нет'}")


async def example_escalation_scenarios():
    """Пример сценариев эскалации"""
    
    community_agent = CommunityConciergeAgent("community_escalation_001")
    
    escalation_test_cases = [
        {
            "content": "Подаю в суд! Нарушили мои права!",
            "expected": "CRITICAL"
        },
        {
            "content": "Жалоба на сервис, требую возврат денег",
            "expected": "HIGH"
        },
        {
            "content": "Как настроить техническую интеграцию с API?",
            "expected": "MEDIUM"
        },
        {
            "content": "Спасибо за помощь!",
            "expected": "NONE"
        },
        {
            "content": "Плохо работает, но терпимо",
            "expected": "LOW"
        }
    ]
    
    print("\n⚠️ COMMUNITY CONCIERGE AGENT - СЦЕНАРИИ ЭСКАЛАЦИИ")
    print("=" * 70)
    
    for i, test_case in enumerate(escalation_test_cases, 1):
        print(f"\n📝 Тест {i}: {test_case['content']}")
        print(f"Ожидаемая эскалация: {test_case['expected']}")
        print("-" * 40)
        
        # Создаем комментарий для анализа
        from .community_concierge_agent import Comment
        
        comment = Comment(
            comment_id=f"test_{i}",
            user_id=f"user_{i}",
            username=f"test_user_{i}",
            content=test_case['content'],
            platform="telegram",
            post_id="test_post",
            timestamp=datetime.now(),
            comment_type=CommentType.GENERAL,
            sentiment=SentimentType.NEUTRAL
        )
        
        # Анализируем комментарий
        analysis = await community_agent._analyze_comment(comment)
        
        # Проверяем необходимость эскалации
        should_escalate = community_agent._should_escalate(comment, analysis)
        
        print(f"😊 Тональность: {analysis['sentiment'].value}")
        print(f"📋 Тип: {analysis['comment_type'].value}")
        print(f"⚠️ Эскалация: {'Да' if should_escalate else 'Нет'}")
        print(f"📊 Уверенность: {analysis['confidence']:.1%}")


async def example_community_statistics():
    """Пример получения статистики сообщества"""
    
    community_agent = CommunityConciergeAgent("community_stats_001")
    
    print("\n📈 COMMUNITY CONCIERGE AGENT - СТАТИСТИКА СООБЩЕСТВА")
    print("=" * 70)
    
    try:
        stats = community_agent.get_community_statistics()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")


async def example_auto_reply_templates():
    """Пример шаблонов автоматических ответов"""
    
    community_agent = CommunityConciergeAgent("community_templates_001")
    
    print("\n🤖 COMMUNITY CONCIERGE AGENT - ШАБЛОНЫ АВТООТВЕТОВ")
    print("=" * 70)
    
    templates = community_agent.auto_reply_templates
    
    for template_name, template_data in templates.items():
        print(f"\n📋 Шаблон: {template_name}")
        print(f"   Текст: {template_data['template']}")
        print(f"   Условия: {', '.join(template_data['conditions'])}")


async def example_moderation_rules():
    """Пример правил модерации"""
    
    community_agent = CommunityConciergeAgent("community_rules_001")
    
    print("\n📜 COMMUNITY CONCIERGE AGENT - ПРАВИЛА МОДЕРАЦИИ")
    print("=" * 70)
    
    rules = community_agent.moderation_rules
    
    print(f"\n🚫 Ключевые слова спама: {len(rules['spam_keywords'])}")
    print(f"   Примеры: {', '.join(rules['spam_keywords'][:5])}")
    
    print(f"\n⚠️ Неподходящие слова: {len(rules['inappropriate_keywords'])}")
    print(f"   Примеры: {', '.join(rules['inappropriate_keywords'][:3])}")
    
    print(f"\n❓ Паттерны вопросов: {len(rules['question_patterns'])}")
    print(f"   Примеры: {', '.join(rules['question_patterns'][:3])}")
    
    print(f"\n😔 Паттерны жалоб: {len(rules['complaint_patterns'])}")
    print(f"   Примеры: {', '.join(rules['complaint_patterns'][:3])}")
    
    print(f"\n😊 Паттерны комплиментов: {len(rules['compliment_patterns'])}")
    print(f"   Примеры: {', '.join(rules['compliment_patterns'][:3])}")


async def main():
    """Главная функция с примерами"""
    
    print("🛡️ COMMUNITY CONCIERGE AGENT - ДЕМОНСТРАЦИЯ ВОЗМОЖНОСТЕЙ")
    print("=" * 80)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Запускаем примеры
        await example_comment_moderation()
        await example_different_configurations()
        await example_sentiment_analysis()
        await example_escalation_scenarios()
        await example_community_statistics()
        await example_auto_reply_templates()
        await example_moderation_rules()
        
        print("\n✅ Все примеры выполнены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка выполнения примеров: {e}")


if __name__ == "__main__":
    # Запускаем примеры
    asyncio.run(main())
