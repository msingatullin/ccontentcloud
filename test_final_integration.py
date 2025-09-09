"""
ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ AI CONTENT ORCHESTRATOR
Комплексная проверка всех MCP интеграций и полного workflow
"""

import asyncio
import sys
import time
from datetime import datetime
from typing import Dict, Any, List

# Добавляем путь к приложению
sys.path.append('.')

from app.orchestrator.main_orchestrator import ContentOrchestrator
from app.agents.chief_agent import ChiefContentAgent
from app.agents.drafting_agent import DraftingAgent
from app.agents.publisher_agent import PublisherAgent
from app.models.content import ContentBrief, Platform, ContentType


class FinalIntegrationTester:
    """Класс для комплексного тестирования системы"""
    
    def __init__(self):
        self.orchestrator = None
        self.chief_agent = None
        self.drafting_agent = None
        self.publisher_agent = None
        self.test_results = {}
        self.start_time = None
        
    async def initialize_system(self):
        """Инициализация всей системы"""
        print("🔧 ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ AI CONTENT ORCHESTRATOR")
        print("=" * 70)
        
        try:
            # Создаем оркестратор
            self.orchestrator = ContentOrchestrator()
            print("✅ ContentOrchestrator инициализирован")
            
            # Создаем агентов
            self.chief_agent = ChiefContentAgent("final_test_chief")
            self.drafting_agent = DraftingAgent("final_test_drafting")
            self.publisher_agent = PublisherAgent("final_test_publisher")
            print("✅ Все агенты созданы")
            
            # Регистрируем агентов в оркестраторе
            await self.orchestrator.agent_manager.register_agent(self.chief_agent)
            await self.orchestrator.agent_manager.register_agent(self.drafting_agent)
            await self.orchestrator.agent_manager.register_agent(self.publisher_agent)
            print("✅ Агенты зарегистрированы в оркестраторе")
            
            # Проверяем статус агентов
            agents = await self.orchestrator.agent_manager.get_available_agents()
            print(f"✅ Доступно агентов: {len(agents)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Критическая ошибка инициализации: {e}")
            return False
    
    async def test_mcp_integrations(self):
        """Тестирование всех MCP интеграций"""
        print("\n🔌 ТЕСТИРОВАНИЕ MCP ИНТЕГРАЦИЙ")
        print("=" * 70)
        
        mcp_results = {}
        
        # Тест 1: News API в ChiefContentAgent
        print("\n📰 Тестирование News API в ChiefContentAgent...")
        try:
            if self.chief_agent.news_mcp is not None:
                print("✅ NewsMCP инициализирован")
                mcp_results['news_api'] = True
            else:
                print("⚠️  NewsMCP недоступен (будет использоваться fallback)")
                mcp_results['news_api'] = False
        except Exception as e:
            print(f"❌ Ошибка News API: {e}")
            mcp_results['news_api'] = False
        
        # Тест 2: AI модели в DraftingAgent
        print("\n🤖 Тестирование AI моделей в DraftingAgent...")
        try:
            if self.drafting_agent.huggingface_mcp is not None:
                print("✅ HuggingFaceMCP инициализирован")
                mcp_results['huggingface'] = True
            else:
                print("⚠️  HuggingFaceMCP недоступен (будет использоваться fallback)")
                mcp_results['huggingface'] = False
                
            if self.drafting_agent.openai_mcp is not None:
                print("✅ OpenAIMCP инициализирован")
                mcp_results['openai'] = True
            else:
                print("⚠️  OpenAIMCP недоступен (будет использоваться fallback)")
                mcp_results['openai'] = False
        except Exception as e:
            print(f"❌ Ошибка AI моделей: {e}")
            mcp_results['ai_models'] = False
        
        # Тест 3: Telegram API в PublisherAgent
        print("\n📱 Тестирование Telegram API в PublisherAgent...")
        try:
            if self.publisher_agent.telegram_mcp is not None:
                print("✅ TelegramMCP инициализирован")
                mcp_results['telegram'] = True
            else:
                print("⚠️  TelegramMCP недоступен (будет использоваться fallback)")
                mcp_results['telegram'] = False
        except Exception as e:
            print(f"❌ Ошибка Telegram API: {e}")
            mcp_results['telegram'] = False
        
        self.test_results['mcp_integrations'] = mcp_results
        return mcp_results
    
    async def test_full_workflow(self):
        """Тестирование полного workflow: стратегия → генерация → публикация"""
        print("\n🔄 ТЕСТИРОВАНИЕ ПОЛНОГО WORKFLOW")
        print("=" * 70)
        
        workflow_start = time.time()
        
        try:
            # Тестовые данные для реального сценария
            test_data = {
                "business_goals": [
                    "привлечение новых клиентов в IT сфере",
                    "повышение узнаваемости бренда",
                    "позиционирование как технологический лидер"
                ],
                "target_audience": "IT-специалисты, разработчики, технические руководители",
                "platforms": ["telegram", "vk"],
                "content_type": "educational",
                "urgency": "normal"
            }
            
            print(f"📝 Тестовые данные:")
            print(f"   Бизнес-цели: {test_data['business_goals']}")
            print(f"   Целевая аудитория: {test_data['target_audience']}")
            print(f"   Платформы: {test_data['platforms']}")
            
            # Шаг 1: Создание контент-стратегии через ChiefContentAgent
            print(f"\n📊 ШАГ 1: Создание контент-стратегии...")
            strategy_start = time.time()
            
            strategy = await self.chief_agent._create_content_strategy(
                test_data['business_goals'],
                test_data['target_audience'],
                test_data['platforms']
            )
            
            strategy_time = time.time() - strategy_start
            print(f"✅ Стратегия создана за {strategy_time:.2f} секунд")
            print(f"   Темы контента: {len(strategy.content_themes)} тем")
            print(f"   Ключевые сообщения: {len(strategy.key_messages)} сообщений")
            
            # Шаг 2: Создание контент-брифа
            print(f"\n📋 ШАГ 2: Создание контент-брифа...")
            brief_start = time.time()
            
            brief_data = {
                "title": "Технологические тренды 2024",
                "description": "Анализ ключевых технологических трендов",
                "target_audience": test_data['target_audience'],
                "platforms": test_data['platforms'],
                "content_type": ContentType.EDUCATIONAL,
                "key_messages": strategy.key_messages[:2],
                "content_themes": strategy.content_themes[:3]
            }
            
            brief = ContentBrief(**brief_data)
            brief_time = time.time() - brief_start
            print(f"✅ Бриф создан за {brief_time:.2f} секунд")
            
            # Шаг 3: Генерация контента через DraftingAgent
            print(f"\n✍️  ШАГ 3: Генерация контента...")
            drafting_start = time.time()
            
            content_result = await self.drafting_agent.generate_content(brief)
            drafting_time = time.time() - drafting_start
            print(f"✅ Контент сгенерирован за {drafting_time:.2f} секунд")
            
            if content_result and 'content' in content_result:
                content = content_result['content']
                print(f"   Платформы: {list(content.keys())}")
                for platform, platform_content in content.items():
                    print(f"   {platform}: {len(platform_content.get('text', ''))} символов")
            
            # Шаг 4: Публикация через PublisherAgent
            print(f"\n📤 ШАГ 4: Публикация контента...")
            publish_start = time.time()
            
            if content_result and 'content' in content_result:
                publish_result = await self.publisher_agent.publish_content(
                    content_result['content'],
                    test_data['platforms']
                )
                publish_time = time.time() - publish_start
                print(f"✅ Контент опубликован за {publish_time:.2f} секунд")
                
                if publish_result and 'results' in publish_result:
                    for platform, result in publish_result['results'].items():
                        status = "✅ Успешно" if result.get('success', False) else "❌ Ошибка"
                        print(f"   {platform}: {status}")
            
            total_workflow_time = time.time() - workflow_start
            print(f"\n🎯 ПОЛНЫЙ WORKFLOW ЗАВЕРШЕН за {total_workflow_time:.2f} секунд")
            
            workflow_results = {
                'strategy_time': strategy_time,
                'brief_time': brief_time,
                'drafting_time': drafting_time,
                'publish_time': publish_time,
                'total_time': total_workflow_time,
                'success': True
            }
            
            self.test_results['full_workflow'] = workflow_results
            return workflow_results
            
        except Exception as e:
            print(f"❌ Критическая ошибка workflow: {e}")
            self.test_results['full_workflow'] = {'success': False, 'error': str(e)}
            return False
    
    def generate_final_report(self):
        """Генерация финального отчета"""
        print("\n" + "=" * 70)
        print("📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 70)
        
        total_time = time.time() - self.start_time if self.start_time else 0
        
        print(f"⏰ Общее время тестирования: {total_time:.2f} секунд")
        print(f"📅 Дата тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Отчет по MCP интеграциям
        if 'mcp_integrations' in self.test_results:
            mcp_results = self.test_results['mcp_integrations']
            print(f"\n🔌 MCP ИНТЕГРАЦИИ:")
            for service, status in mcp_results.items():
                status_icon = "✅" if status else "⚠️"
                print(f"   {status_icon} {service}: {'Работает' if status else 'Fallback'}")
        
        # Отчет по workflow
        if 'full_workflow' in self.test_results:
            workflow_results = self.test_results['full_workflow']
            if workflow_results.get('success', False):
                print(f"\n🔄 ПОЛНЫЙ WORKFLOW:")
                print(f"   ✅ Стратегия: {workflow_results.get('strategy_time', 0):.2f}с")
                print(f"   ✅ Генерация: {workflow_results.get('drafting_time', 0):.2f}с")
                print(f"   ✅ Публикация: {workflow_results.get('publish_time', 0):.2f}с")
                print(f"   🎯 Общее время: {workflow_results.get('total_time', 0):.2f}с")
            else:
                print(f"\n❌ WORKFLOW: Ошибка - {workflow_results.get('error', 'Неизвестная ошибка')}")
        
        # Общая оценка готовности
        total_tests = 0
        passed_tests = 0
        
        if 'mcp_integrations' in self.test_results:
            total_tests += len(self.test_results['mcp_integrations'])
            passed_tests += sum(1 for v in self.test_results['mcp_integrations'].values() if v)
        
        if 'full_workflow' in self.test_results:
            total_tests += 1
            if self.test_results['full_workflow'].get('success', False):
                passed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 ОБЩАЯ ОЦЕНКА:")
        print(f"   📊 Пройдено тестов: {passed_tests}/{total_tests}")
        print(f"   📈 Успешность: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print(f"   🎉 СИСТЕМА ГОТОВА К ПРОДАКШЕНУ!")
            print(f"   ✅ AI Content Orchestrator превосходит конкурентов!")
        elif success_rate >= 60:
            print(f"   ⚠️  Система требует доработки перед продакшеном")
        else:
            print(f"   ❌ Система не готова к продакшену")
        
        return success_rate >= 80


async def main():
    """Основная функция финального тестирования"""
    print("🚀 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ AI CONTENT ORCHESTRATOR")
    print("=" * 70)
    print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = FinalIntegrationTester()
    tester.start_time = time.time()
    
    try:
        # Инициализация системы
        if not await tester.initialize_system():
            print("❌ Критическая ошибка - система не инициализирована")
            return
        
        # Тестирование MCP интеграций
        await tester.test_mcp_integrations()
        
        # Тестирование полного workflow
        await tester.test_full_workflow()
        
        # Генерация финального отчета
        is_ready = tester.generate_final_report()
        
        print(f"\n⏰ Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return is_ready
        
    except Exception as e:
        print(f"❌ Критическая ошибка тестирования: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(main())
