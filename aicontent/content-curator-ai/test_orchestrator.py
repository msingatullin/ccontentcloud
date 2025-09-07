#!/usr/bin/env python3
"""
Тест главного оркестратора
Проверяет базовую функциональность системы
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.orchestrator.main_orchestrator import ContentOrchestrator
from app.orchestrator.agent_manager import BaseAgent, AgentCapability
from app.orchestrator.workflow_engine import TaskType, TaskPriority
from app.models.content import ContentBrief, Platform, ContentType


class MockAgent(BaseAgent):
    """Мок-агент для тестирования"""
    
    def __init__(self, agent_id: str, name: str):
        capability = AgentCapability(
            task_types=[TaskType.PLANNED, TaskType.REAL_TIME],
            max_concurrent_tasks=2,
            specializations=["content_creation"],
            performance_score=1.0
        )
        super().__init__(agent_id, name, capability)
    
    async def execute_task(self, task):
        """Мок-выполнение задачи"""
        print(f"🤖 {self.name} выполняет задачу: {task.name}")
        
        # Имитируем работу
        await asyncio.sleep(0.1)
        
        # Возвращаем результат
        return {
            "task_id": task.id,
            "agent_id": self.agent_id,
            "result": f"Контент создан для {task.context.get('platform', 'unknown')}",
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }


async def test_orchestrator():
    """Тестирует главный оркестратор"""
    print("🚀 Начинаем тестирование ContentOrchestrator")
    
    # Создаем оркестратор
    orchestrator = ContentOrchestrator()
    
    # Создаем мок-агентов
    agent1 = MockAgent("agent_1", "Chief Content Agent")
    agent2 = MockAgent("agent_2", "Drafting Agent")
    agent3 = MockAgent("agent_3", "Publisher Agent")
    
    # Регистрируем агентов
    print("📝 Регистрируем агентов...")
    orchestrator.register_agent(agent1)
    orchestrator.register_agent(agent2)
    orchestrator.register_agent(agent3)
    
    # Запускаем оркестратор
    print("▶️ Запускаем оркестратор...")
    await orchestrator.start()
    
    # Проверяем статус системы
    print("📊 Статус системы:")
    status = orchestrator.get_system_status()
    print(f"  - Оркестратор запущен: {status['orchestrator']['is_running']}")
    print(f"  - Всего агентов: {status['agents']['total_agents']}")
    print(f"  - Активных задач: {status['agents']['active_tasks']}")
    
    # Создаем тестовый запрос
    print("📝 Создаем тестовый запрос...")
    request = {
        "title": "Тестовый пост о AI",
        "description": "Пост о возможностях искусственного интеллекта",
        "target_audience": "IT-специалисты",
        "business_goals": ["привлечение внимания", "образование"],
        "call_to_action": "Подписывайтесь на канал",
        "tone": "professional",
        "keywords": ["AI", "искусственный интеллект", "технологии"],
        "platforms": ["telegram", "vk"],
        "content_types": ["post"]
    }
    
    # Обрабатываем запрос
    print("⚙️ Обрабатываем запрос...")
    result = await orchestrator.process_content_request(request)
    
    if result["success"]:
        print("✅ Запрос успешно обработан!")
        print(f"  - Workflow ID: {result['workflow_id']}")
        print(f"  - Brief ID: {result['brief_id']}")
        print(f"  - Статус: {result['result']['status']}")
        print(f"  - Выполнено задач: {result['result']['completed_tasks']}")
        print(f"  - Провалено задач: {result['result']['failed_tasks']}")
    else:
        print(f"❌ Ошибка обработки запроса: {result['error']}")
    
    # Проверяем финальный статус
    print("📊 Финальный статус системы:")
    final_status = orchestrator.get_system_status()
    print(f"  - Всего агентов: {final_status['agents']['total_agents']}")
    print(f"  - Выполнено задач: {final_status['agents']['completed_tasks']}")
    print(f"  - Активных задач: {final_status['agents']['active_tasks']}")
    
    # Останавливаем оркестратор
    print("⏹️ Останавливаем оркестратор...")
    await orchestrator.stop()
    
    print("🎉 Тестирование завершено!")


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
