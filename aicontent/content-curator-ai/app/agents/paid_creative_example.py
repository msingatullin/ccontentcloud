"""
Пример использования Paid Creative Agent
Демонстрирует возможности создания рекламных креативов и оптимизации
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from .paid_creative_agent import PaidCreativeAgent, AdPlatform, AdFormat, AdObjective, ComplianceStatus
from .paid_creative_config import load_config_from_env, SOCIAL_MEDIA_FOCUS_CONFIG, SEARCH_ENGINE_FOCUS_CONFIG, VIDEO_FOCUS_CONFIG, ALL_PLATFORMS_CONFIG


async def example_create_ad_creatives():
    """Пример создания рекламных креативов"""
    
    # Создаем агента с конфигурацией по умолчанию
    paid_creative_agent = PaidCreativeAgent("paid_creative_001")
    
    # Примеры задач для создания креативов
    test_tasks = [
        {
            "task_type": "create_creative",
            "platform": "telegram_ads",
            "objective": "awareness",
            "product": "AI-помощник для бизнеса",
            "target_audience": "предприниматели 25-45 лет",
            "budget": 10000.0,
            "landing_page": "https://example.com/ai-assistant",
            "keywords": ["AI", "автоматизация", "бизнес"],
            "hashtags": ["#AI", "#бизнес", "#автоматизация"]
        },
        {
            "task_type": "create_creative",
            "platform": "vk_ads",
            "objective": "leads",
            "product": "курс по маркетингу",
            "target_audience": "маркетологи 22-35 лет",
            "budget": 5000.0,
            "landing_page": "https://example.com/marketing-course",
            "keywords": ["маркетинг", "курс", "обучение"],
            "hashtags": ["#маркетинг", "#курс", "#обучение"]
        },
        {
            "task_type": "create_creative",
            "platform": "google_ads",
            "objective": "sales",
            "product": "CRM система",
            "target_audience": "владельцы бизнеса 30-50 лет",
            "budget": 15000.0,
            "landing_page": "https://example.com/crm",
            "keywords": ["CRM", "управление клиентами", "продажи"],
            "hashtags": ["#CRM", "#продажи", "#бизнес"]
        },
        {
            "task_type": "create_creative",
            "platform": "facebook_ads",
            "objective": "engagement",
            "product": "мобильное приложение",
            "target_audience": "пользователи смартфонов 18-40 лет",
            "budget": 8000.0,
            "landing_page": "https://example.com/app",
            "keywords": ["приложение", "мобильный", "удобство"],
            "hashtags": ["#приложение", "#мобильный", "#удобство"]
        }
    ]
    
    print("🎯 PAID CREATIVE AGENT - ПРИМЕРЫ СОЗДАНИЯ РЕКЛАМНЫХ КРЕАТИВОВ")
    print("=" * 80)
    
    for i, task_data in enumerate(test_tasks, 1):
        print(f"\n📝 Задача {i}: Создание креатива для {task_data['platform']}")
        print(f"Цель: {task_data['objective']}")
        print(f"Продукт: {task_data['product']}")
        print(f"Аудитория: {task_data['target_audience']}")
        print(f"Бюджет: {task_data['budget']} руб.")
        print("-" * 60)
        
        # Создаем задачу
        from app.orchestrator.workflow_engine import Task, TaskType
        
        task = Task(
            name=f"create_creative_{i}",
            task_type=TaskType.PLANNED,
            context=task_data
        )
        
        try:
            # Выполняем создание креатива
            result = await paid_creative_agent.execute_task(task)
            
            # Выводим результаты
            print(f"🆔 ID креатива: {result['creative_id']}")
            print(f"📱 Платформа: {result['platform']}")
            print(f"🎯 Цель: {result['objective']}")
            print(f"📰 Заголовок: {result['headline']}")
            print(f"📝 Описание: {result['description']}")
            print(f"🔔 CTA: {result['call_to_action']}")
            print(f"👥 Аудитория: {result['target_audience']}")
            print(f"💰 Бюджет: {result['budget']} руб.")
            
            # Статус соответствия
            compliance = result['compliance_report']
            print(f"✅ Статус соответствия: {result['compliance_status']}")
            print(f"⚠️ Риск: {compliance['risk_score']:.1%}")
            
            if compliance['violations']:
                print(f"❌ Нарушения: {', '.join(compliance['violations'])}")
            
            if compliance['recommendations']:
                print(f"💡 Рекомендации: {', '.join(compliance['recommendations'])}")
            
            print(f"📅 Создан: {result['created_at']}")
                    
        except Exception as e:
            print(f"❌ Ошибка при создании креатива: {e}")
        
        print()


async def example_ab_testing():
    """Пример A/B тестирования рекламных креативов"""
    
    paid_creative_agent = PaidCreativeAgent("paid_creative_ab_001")
    
    print("\n🧪 PAID CREATIVE AGENT - A/B ТЕСТИРОВАНИЕ")
    print("=" * 80)
    
    # Создаем A/B тест
    ab_test_data = {
        "task_type": "ab_test",
        "test_name": "Тест заголовков для AI-помощника",
        "variants": [
            {
                "creative": {
                    "platform": "telegram_ads",
                    "objective": "awareness",
                    "product": "AI-помощник для бизнеса",
                    "target_audience": "предприниматели 25-45 лет",
                    "budget": 5000.0
                },
                "traffic_percentage": 50.0,
                "is_control": True
            },
            {
                "creative": {
                    "platform": "telegram_ads",
                    "objective": "awareness",
                    "product": "AI-помощник для бизнеса",
                    "target_audience": "предприниматели 25-45 лет",
                    "budget": 5000.0
                },
                "traffic_percentage": 50.0,
                "is_control": False
            }
        ]
    }
    
    # Создаем задачу
    from app.orchestrator.workflow_engine import Task, TaskType
    
    task = Task(
        name="create_ab_test",
        task_type=TaskType.COMPLEX,
        context=ab_test_data
    )
    
    try:
        # Выполняем создание A/B теста
        result = await paid_creative_agent.execute_task(task)
        
        print(f"🆔 ID теста: {result['test_id']}")
        print(f"📝 Название: {result['test_name']}")
        print(f"📅 Начало: {result['start_date']}")
        print(f"📊 Статус: {result['status']}")
        
        print(f"\n📋 Варианты теста:")
        for variant in result['variants']:
            print(f"   {variant['variant_id']}: {variant['traffic_percentage']}% трафика")
            print(f"   Контрольный: {'Да' if variant['is_control'] else 'Нет'}")
            print(f"   ID креатива: {variant['creative_id']}")
            print()
                    
    except Exception as e:
        print(f"❌ Ошибка при создании A/B теста: {e}")


async def example_optimization():
    """Пример оптимизации рекламного креатива"""
    
    paid_creative_agent = PaidCreativeAgent("paid_creative_opt_001")
    
    print("\n⚡ PAID CREATIVE AGENT - ОПТИМИЗАЦИЯ КРЕАТИВОВ")
    print("=" * 80)
    
    # Создаем креатив для оптимизации
    creative_data = {
        "task_type": "create_creative",
        "platform": "telegram_ads",
        "objective": "sales",
        "product": "онлайн-курс",
        "target_audience": "студенты 18-25 лет",
        "budget": 3000.0
    }
    
    # Создаем задачу для создания креатива
    from app.orchestrator.workflow_engine import Task, TaskType
    
    create_task = Task(
        name="create_creative_for_optimization",
        task_type=TaskType.PLANNED,
        context=creative_data
    )
    
    try:
        # Создаем креатив
        creative_result = await paid_creative_agent.execute_task(create_task)
        creative_id = creative_result['creative_id']
        
        print(f"📝 Создан креатив: {creative_id}")
        print(f"📰 Заголовок: {creative_result['headline']}")
        print(f"📝 Описание: {creative_result['description']}")
        
        # Теперь оптимизируем его
        optimization_data = {
            "task_type": "optimize_creative",
            "creative_id": creative_id,
            "performance_data": {
                "impressions": 10000,
                "clicks": 150,
                "conversions": 5,
                "cost": 500.0,
                "ctr": 0.015,  # 1.5%
                "cpc": 3.33,
                "cpm": 50.0,
                "conversion_rate": 0.033,  # 3.3%
                "cost_per_conversion": 100.0,
                "roi": 2.0,
                "roas": 2.0
            }
        }
        
        # Создаем задачу для оптимизации
        optimize_task = Task(
            name="optimize_creative",
            task_type=TaskType.PLANNED,
            context=optimization_data
        )
        
        # Выполняем оптимизацию
        optimization_result = await paid_creative_agent.execute_task(optimize_task)
        
        print(f"\n📊 Текущие метрики:")
        metrics = optimization_result['current_metrics']
        print(f"   CTR: {metrics['ctr']:.1%}")
        print(f"   Конверсия: {metrics['conversion_rate']:.1%}")
        print(f"   CPC: {metrics['cpc']:.2f} руб.")
        print(f"   ROI: {metrics['roi']:.1f}")
        
        print(f"\n🔧 Области для оптимизации:")
        for optimization in optimization_result['optimizations']:
            print(f"   - {optimization}")
        
        print(f"\n💡 Рекомендации:")
        for recommendation in optimization_result['recommendations']:
            print(f"   - {recommendation}")
        
        print(f"\n📅 Оптимизирован: {optimization_result['optimized_at']}")
                    
    except Exception as e:
        print(f"❌ Ошибка при оптимизации: {e}")


async def example_compliance_check():
    """Пример проверки соответствия политикам"""
    
    paid_creative_agent = PaidCreativeAgent("paid_creative_compliance_001")
    
    print("\n🛡️ PAID CREATIVE AGENT - ПРОВЕРКА СООТВЕТСТВИЯ ПОЛИТИКАМ")
    print("=" * 80)
    
    # Создаем креатив для проверки
    creative_data = {
        "task_type": "create_creative",
        "platform": "google_ads",
        "objective": "sales",
        "product": "криптовалютный курс",
        "target_audience": "инвесторы 25-45 лет",
        "budget": 2000.0
    }
    
    # Создаем задачу для создания креатива
    from app.orchestrator.workflow_engine import Task, TaskType
    
    create_task = Task(
        name="create_creative_for_compliance",
        task_type=TaskType.PLANNED,
        context=creative_data
    )
    
    try:
        # Создаем креатив
        creative_result = await paid_creative_agent.execute_task(create_task)
        creative_id = creative_result['creative_id']
        
        print(f"📝 Создан креатив: {creative_id}")
        print(f"📰 Заголовок: {creative_result['headline']}")
        print(f"📝 Описание: {creative_result['description']}")
        
        # Проверяем соответствие политикам
        compliance_data = {
            "task_type": "check_compliance",
            "creative_id": creative_id
        }
        
        # Создаем задачу для проверки
        compliance_task = Task(
            name="check_compliance",
            task_type=TaskType.PLANNED,
            context=compliance_data
        )
        
        # Выполняем проверку
        compliance_result = await paid_creative_agent.execute_task(compliance_task)
        
        print(f"\n✅ Статус соответствия: {compliance_result['compliance_status']}")
        print(f"⚠️ Уровень риска: {compliance_result['risk_score']:.1%}")
        
        if compliance_result['violations']:
            print(f"\n❌ Нарушения:")
            for violation in compliance_result['violations']:
                print(f"   - {violation}")
        
        if compliance_result['recommendations']:
            print(f"\n💡 Рекомендации:")
            for recommendation in compliance_result['recommendations']:
                print(f"   - {recommendation}")
        
        print(f"\n📅 Проверен: {compliance_result['checked_at']}")
                    
    except Exception as e:
        print(f"❌ Ошибка при проверке соответствия: {e}")


async def example_different_configurations():
    """Пример работы с разными конфигурациями"""
    
    print("\n⚙️ PAID CREATIVE AGENT - РАЗНЫЕ КОНФИГУРАЦИИ")
    print("=" * 80)
    
    configs = [
        ("Стандартная", load_config_from_env()),
        ("Социальные сети", SOCIAL_MEDIA_FOCUS_CONFIG),
        ("Поисковые системы", SEARCH_ENGINE_FOCUS_CONFIG),
        ("Видео платформы", VIDEO_FOCUS_CONFIG),
        ("Все платформы", ALL_PLATFORMS_CONFIG)
    ]
    
    for config_name, config in configs:
        print(f"\n🔧 Конфигурация: {config_name}")
        print(f"   Агент: {config.agent_name}")
        print(f"   Максимум задач: {config.max_concurrent_tasks}")
        print(f"   Производительность: {config.performance_score}")
        print(f"   Создание креативов: {config.creative.enabled}")
        print(f"   Соответствие политикам: {config.compliance.enabled}")
        print(f"   A/B тестирование: {config.ab_testing.enabled}")
        print(f"   Оптимизация: {config.optimization.enabled}")
        
        # Показываем включенные платформы
        enabled_platforms = [
            platform.value for platform, platform_config in config.platforms.items()
            if platform_config.enabled
        ]
        print(f"   Включенные платформы: {', '.join(enabled_platforms)}")


async def example_platform_guidelines():
    """Пример руководящих принципов платформ"""
    
    paid_creative_agent = PaidCreativeAgent("paid_creative_guidelines_001")
    
    print("\n📋 PAID CREATIVE AGENT - РУКОВОДЯЩИЕ ПРИНЦИПЫ ПЛАТФОРМ")
    print("=" * 80)
    
    platforms = [
        ("Telegram Ads", AdPlatform.TELEGRAM_ADS),
        ("VK Ads", AdPlatform.VK_ADS),
        ("Google Ads", AdPlatform.GOOGLE_ADS),
        ("Yandex Direct", AdPlatform.YANDEX_DIRECT),
        ("Facebook Ads", AdPlatform.FACEBOOK_ADS),
        ("Instagram Ads", AdPlatform.INSTAGRAM_ADS),
        ("YouTube Ads", AdPlatform.YOUTUBE_ADS),
        ("TikTok Ads", AdPlatform.TIKTOK_ADS)
    ]
    
    for platform_name, platform in platforms:
        print(f"\n🔧 {platform_name} ({platform.value})")
        guidelines = paid_creative_agent.platform_guidelines.get(platform, {})
        
        if guidelines:
            print(f"   Максимальная длина заголовка: {guidelines.get('max_headline_length', 'N/A')}")
            print(f"   Максимальная длина описания: {guidelines.get('max_description_length', 'N/A')}")
            print(f"   Максимальная длина CTA: {guidelines.get('max_cta_length', 'N/A')}")
            print(f"   Разрешенные форматы: {len(guidelines.get('allowed_formats', []))}")
            print(f"   Запрещенный контент: {len(guidelines.get('prohibited_content', []))}")
            print(f"   Обязательные элементы: {', '.join(guidelines.get('required_elements', []))}")
            print(f"   Опции таргетинга: {', '.join(guidelines.get('targeting_options', []))}")


async def example_performance_statistics():
    """Пример получения статистики производительности"""
    
    paid_creative_agent = PaidCreativeAgent("paid_creative_stats_001")
    
    print("\n📈 PAID CREATIVE AGENT - СТАТИСТИКА ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 80)
    
    try:
        stats = paid_creative_agent.get_performance_statistics()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")


async def main():
    """Главная функция с примерами"""
    
    print("🎯 PAID CREATIVE AGENT - ДЕМОНСТРАЦИЯ ВОЗМОЖНОСТЕЙ")
    print("=" * 80)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Запускаем примеры
        await example_create_ad_creatives()
        await example_ab_testing()
        await example_optimization()
        await example_compliance_check()
        await example_different_configurations()
        await example_platform_guidelines()
        await example_performance_statistics()
        
        print("\n✅ Все примеры выполнены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка выполнения примеров: {e}")


if __name__ == "__main__":
    # Запускаем примеры
    asyncio.run(main())
