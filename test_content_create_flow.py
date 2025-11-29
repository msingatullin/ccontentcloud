#!/usr/bin/env python3
"""
Тестовый скрипт для проверки flow создания и публикации контента в Telegram
"""

import requests
import json
import time
import sys

# Конфигурация
API_URL = "https://content-curator-dt3n7kzpwq-uc.a.run.app"
# API_URL = "http://localhost:8080"  # Для локального тестирования

# Тестовые данные пользователя (нужен реальный JWT токен)
TEST_TOKEN = None  # Будет получен через /auth/login или передан как аргумент


def print_section(title):
    """Печатает секцию с заголовком"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_health_check():
    """Проверяет доступность API"""
    print_section("1. Health Check")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_create_content(token):
    """Тестирует создание контента"""
    print_section("2. Create Content Request")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Тестовый запрос на создание контента
    payload = {
        "title": "Тестовый пост о AI технологиях",
        "description": "Краткий обзор последних достижений в области искусственного интеллекта",
        "target_audience": "Разработчики и технические специалисты",
        "business_goals": ["Увеличить вовлеченность", "Показать экспертизу"],
        "platforms": ["telegram"],
        "content_types": ["post"],
        "tone": "professional",
        "keywords": ["AI", "машинное обучение", "технологии"],
        "test_mode": True  # ВАЖНО: тестовый режим
    }
    
    print("Request:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            f"{API_URL}/api/v1/content/create",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"\nStatus: {response.status_code}")
        print(f"Response:")
        response_data = response.json()
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        
        if response.status_code == 200 and response_data.get("success"):
            print("\n✅ Контент создан успешно!")
            workflow_id = response_data.get("workflow_id")
            return True, workflow_id
        else:
            print(f"\n❌ Ошибка создания контента")
            return False, None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False, None


def test_workflow_status(token, workflow_id):
    """Проверяет статус workflow"""
    print_section(f"3. Workflow Status: {workflow_id}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{API_URL}/api/v1/workflow/{workflow_id}/status",
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response:")
        response_data = response.json()
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        
        return response.status_code == 200
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_me_endpoint(token):
    """Проверяет эндпоинт /me для получения социальных сетей пользователя"""
    print_section("0. User Profile & Social Media")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{API_URL}/api/v1/auth/me",
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"User: {user_data.get('email')}")
            print(f"Username: {user_data.get('username')}")
            social_media = user_data.get('socialMedia', [])
            print(f"\nSocial Media Accounts: {len(social_media)}")
            for sm in social_media:
                print(f"  - {sm.get('name')}: active={sm.get('isActive')}")
                if sm.get('name') == 'Telegram':
                    metadata = sm.get('metadata', {})
                    print(f"    Channel: {metadata.get('channelName')}")
                    print(f"    Link: {metadata.get('channelLink')}")
            
            if len(social_media) == 0:
                print("\n⚠️  ПРЕДУПРЕЖДЕНИЕ: У пользователя нет подключенных социальных сетей!")
                print("   Для тестирования публикации в Telegram нужно:")
                print("   1. Подключить Telegram канал через /api/v1/telegram/auth")
                print("   2. Или создать тестовый канал в БД")
            
            return response.status_code == 200
        else:
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def main():
    """Основная функция"""
    print("\n" + "="*60)
    print("  ТЕСТ FLOW: Создание контента -> Публикация в Telegram")
    print("="*60)
    
    # Получаем токен из аргументов или переменной окружения
    token = None
    if len(sys.argv) > 1:
        token = sys.argv[1]
    
    if not token:
        print("\n❌ Ошибка: не указан JWT токен")
        print("\nИспользование:")
        print(f"  python3 {sys.argv[0]} <JWT_TOKEN>")
        print("\nИли получите токен через:")
        print(f"  curl -X POST {API_URL}/api/v1/auth/login \\")
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"email": "your@email.com", "password": "password"}\'')
        sys.exit(1)
    
    # Выполняем тесты
    results = []
    
    # 1. Health check
    results.append(("Health Check", test_health_check()))
    
    # 2. Проверка пользователя и социальных сетей
    results.append(("User Profile", test_me_endpoint(token)))
    
    # 3. Создание контента
    success, workflow_id = test_create_content(token)
    results.append(("Create Content", success))
    
    # 4. Проверка статуса workflow (если создание прошло успешно)
    if success and workflow_id:
        time.sleep(2)  # Даем время на обработку
        results.append(("Workflow Status", test_workflow_status(token, workflow_id)))
    
    # Итоги
    print_section("РЕЗУЛЬТАТЫ ТЕСТОВ")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}  {test_name}")
    
    print(f"\n{'='*60}")
    print(f"  Пройдено: {passed}/{total}")
    print(f"{'='*60}\n")
    
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()

