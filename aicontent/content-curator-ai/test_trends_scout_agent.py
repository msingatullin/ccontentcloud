#!/usr/bin/env python3
"""
Тестирование TrendsScoutAgent
Проверка функциональности агента анализа трендов
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.trends_scout_agent import TrendsScoutAgent, TrendData, TrendType, TrendStatus
from app.agents.trend_analyzer import TrendAnalyzer
from app.orchestrator.workflow_engine import Task, TaskType, TaskPriority

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrendsScoutTester:
    """Класс для тестирования TrendsScoutAgent"""
    
    def __init__(self):
        self.trends_agent = None
        self.trend_analyzer = None
        
    async def initialize_agents(self):
        """Инициализация агентов"""
        print("🔧 ИНИЦИАЛИЗАЦИЯ TRENDS SCOUT AGENT")
        print("=" * 50)
        
        try:
            # Создаем TrendsScoutAgent
            self.trends_agent = TrendsScoutAgent("test_trends_scout")
            print("✅ TrendsScoutAgent создан")
            
            # Создаем TrendAnalyzer
            self.trend_analyzer = TrendAnalyzer()
            print("✅ TrendAnalyzer создан")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка инициализации: {e}")
            return False
    
    async def test_trend_analysis(self):
        """Тестирование анализа трендов"""
        print("\n📊 ТЕСТИРОВАНИЕ АНАЛИЗА ТРЕНДОВ")
        print("=" * 50)
        
        try:
            # Создаем тестовые данные тренда
            test_trend_data = {
                'trend_id': 'test_trend_1',
                'title': 'Искусственный интеллект в образовании',
                'description': 'Новые технологии ИИ меняют подход к обучению и образованию',
                'trend_type': 'news',
                'status': 'rising',
                'popularity_score': 85.0,
                'engagement_rate': 78.0,
                'growth_rate': 25.0,
                'source': 'TechNews',
                'keywords': ['ИИ', 'образование', 'технологии'],
                'hashtags': ['#ИИ', '#образование', '#технологии'],
                'target_audience': ['tech_audience', 'general_audience'],
                'content_ideas': [
                    'Объяснить как ИИ помогает в обучении',
                    'Показать примеры использования ИИ в школах'
                ],
                'discovered_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            
            # Анализируем тренд
            analysis = self.trend_analyzer.analyze_trend(test_trend_data, 'tech_audience')
            
            print(f"📈 Анализ тренда: {test_trend_data['title']}")
            print(f"   Общий балл: {analysis.overall_score:.2f}")
            print(f"   Уровень тренда: {analysis.trend_level.value}")
            print(f"   Уверенность: {analysis.confidence_level:.2f}%")
            print(f"   Потенциал вирусности: {analysis.metrics.virality_potential:.2f}")
            print(f"   Релевантность аудитории: {analysis.metrics.audience_relevance:.2f}")
            print(f"   Потенциал контента: {analysis.metrics.content_potential:.2f}")
            print(f"   Время жизни тренда: {analysis.metrics.trend_lifetime:.1f} часов")
            
            print(f"\n💪 Сильные стороны:")
            for strength in analysis.strengths:
                print(f"   ✅ {strength}")
            
            print(f"\n⚠️ Слабые стороны:")
            for weakness in analysis.weaknesses:
                print(f"   ❌ {weakness}")
            
            print(f"\n🎯 Возможности:")
            for opportunity in analysis.opportunities:
                print(f"   🚀 {opportunity}")
            
            print(f"\n📋 Рекомендации:")
            for recommendation in analysis.recommendations:
                print(f"   💡 {recommendation}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка анализа трендов: {e}")
            return False
    
    async def test_trends_agent_execution(self):
        """Тестирование выполнения задач TrendsScoutAgent"""
        print("\n🤖 ТЕСТИРОВАНИЕ ВЫПОЛНЕНИЯ ЗАДАЧ")
        print("=" * 50)
        
        try:
            # Создаем задачу для анализа общих трендов
            task = Task(
                task_id="test_trends_analysis",
                task_type=TaskType.REAL_TIME,
                priority=TaskPriority.HIGH,
                parameters={
                    'analysis_type': 'general',
                    'time_period': '1h',
                    'target_audience': 'tech_audience'
                }
            )
            
            print(f"📋 Выполнение задачи: {task.task_id}")
            print(f"   Тип анализа: {task.parameters['analysis_type']}")
            print(f"   Период: {task.parameters['time_period']}")
            print(f"   Целевая аудитория: {task.parameters['target_audience']}")
            
            # Выполняем задачу
            result = await self.trends_agent.execute_task(task)
            
            if result['status'] == 'success':
                print("✅ Задача выполнена успешно")
                print(f"   Время выполнения: {result['execution_time']}")
                
                # Анализируем результат
                analysis_result = result['result']
                print(f"\n📊 Результаты анализа:")
                print(f"   ID отчета: {analysis_result.report_id}")
                print(f"   Период анализа: {analysis_result.analysis_period}")
                print(f"   Всего трендов: {analysis_result.total_trends}")
                print(f"   Вирусный контент: {len(analysis_result.viral_content)}")
                print(f"   Рекомендации: {len(analysis_result.content_recommendations)}")
                
                print(f"\n🎯 Топ рекомендации:")
                for i, rec in enumerate(analysis_result.content_recommendations[:3], 1):
                    print(f"   {i}. {rec}")
                
                print(f"\n📈 Инсайты аудитории:")
                insights = analysis_result.audience_insights
                print(f"   Средняя вовлеченность: {insights.get('average_engagement', 0):.2f}")
                print(f"   Средний рост: {insights.get('average_growth_rate', 0):.2f}%")
                print(f"   Топ ключевые слова: {', '.join(insights.get('top_keywords', [])[:3])}")
                
                return True
            else:
                print(f"❌ Ошибка выполнения задачи: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка тестирования выполнения задач: {e}")
            return False
    
    async def test_viral_content_analysis(self):
        """Тестирование анализа вирусного контента"""
        print("\n🔥 ТЕСТИРОВАНИЕ АНАЛИЗА ВИРУСНОГО КОНТЕНТА")
        print("=" * 50)
        
        try:
            # Создаем задачу для анализа вирусного контента
            task = Task(
                task_id="test_viral_analysis",
                task_type=TaskType.REAL_TIME,
                priority=TaskPriority.HIGH,
                parameters={
                    'analysis_type': 'viral_content',
                    'time_period': '1h',
                    'target_audience': 'general_audience'
                }
            )
            
            print(f"📋 Анализ вирусного контента")
            
            # Выполняем задачу
            result = await self.trends_agent.execute_task(task)
            
            if result['status'] == 'success':
                print("✅ Анализ вирусного контента выполнен")
                
                analysis_result = result['result']
                print(f"   Вирусных трендов найдено: {len(analysis_result.viral_content)}")
                
                if analysis_result.viral_content:
                    print(f"\n🔥 Топ вирусные тренды:")
                    for i, trend in enumerate(analysis_result.viral_content[:3], 1):
                        print(f"   {i}. {trend.title}")
                        print(f"      Популярность: {trend.popularity_score:.1f}")
                        print(f"      Вовлеченность: {trend.engagement_rate:.1f}")
                        print(f"      Рост: {trend.growth_rate:.1f}%")
                
                return True
            else:
                print(f"❌ Ошибка анализа вирусного контента: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка тестирования вирусного контента: {e}")
            return False
    
    async def test_agent_capabilities(self):
        """Тестирование возможностей агента"""
        print("\n⚙️ ТЕСТИРОВАНИЕ ВОЗМОЖНОСТЕЙ АГЕНТА")
        print("=" * 50)
        
        try:
            agent = self.trends_agent
            
            print(f"🤖 Агент: {agent.name}")
            print(f"   ID: {agent.agent_id}")
            print(f"   Статус: {agent.status.value}")
            print(f"   Типы задач: {[t.value for t in agent.capabilities.task_types]}")
            print(f"   Макс. параллельных задач: {agent.capabilities.max_concurrent_tasks}")
            print(f"   Специализации: {agent.capabilities.specializations}")
            print(f"   Коэффициент производительности: {agent.capabilities.performance_score}")
            
            # Проверяем MCP интеграции
            print(f"\n🔌 MCP интеграции:")
            print(f"   News MCP: {'✅' if agent.news_mcp else '❌'}")
            print(f"   Twitter MCP: {'✅' if agent.twitter_mcp else '❌'}")
            print(f"   Google Trends MCP: {'✅' if agent.google_trends_mcp else '❌'}")
            
            # Проверяем TrendAnalyzer
            print(f"   TrendAnalyzer: {'✅' if agent.trend_analyzer else '❌'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования возможностей: {e}")
            return False
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ TRENDS SCOUT AGENT")
        print("=" * 60)
        
        tests = [
            ("Инициализация агентов", self.initialize_agents),
            ("Возможности агента", self.test_agent_capabilities),
            ("Анализ трендов", self.test_trend_analysis),
            ("Выполнение задач", self.test_trends_agent_execution),
            ("Анализ вирусного контента", self.test_viral_content_analysis)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n🧪 {test_name}...")
            try:
                result = await test_func()
                results.append((test_name, result))
                if result:
                    print(f"✅ {test_name} - ПРОЙДЕН")
                else:
                    print(f"❌ {test_name} - ПРОВАЛЕН")
            except Exception as e:
                print(f"❌ {test_name} - ОШИБКА: {e}")
                results.append((test_name, False))
        
        # Итоговый отчет
        print("\n" + "=" * 60)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"   {test_name}: {status}")
        
        print(f"\n🎯 Результат: {passed}/{total} тестов пройдено")
        
        if passed == total:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            return True
        else:
            print("⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
            return False


async def main():
    """Главная функция"""
    tester = TrendsScoutTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎊 TrendsScoutAgent готов к работе!")
        sys.exit(0)
    else:
        print("\n💥 Обнаружены проблемы с TrendsScoutAgent")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
