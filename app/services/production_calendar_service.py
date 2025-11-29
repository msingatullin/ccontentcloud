"""
Сервис для работы с производственным календарем
Интеграция с API production-calendar.ru
"""

import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime, date

logger = logging.getLogger(__name__)

# API токен для production-calendar.ru
PRODUCTION_CALENDAR_TOKEN = "8f3d2a1b8a651e94149cbc4cc2c332fa"
PRODUCTION_CALENDAR_BASE_URL = "https://production-calendar.ru"

class ProductionCalendarService:
    """Сервис для работы с производственным календарем"""
    
    @staticmethod
    def is_working_day(check_date: date, country: str = 'ru') -> bool:
        """
        Проверяет, является ли день рабочим
        
        Args:
            check_date: Дата для проверки
            country: Код страны (ru, by, kz)
        
        Returns:
            True если рабочий день, False если выходной/праздничный
        """
        try:
            # Форматируем дату в формат ДД.ММ.ГГГГ
            date_str = check_date.strftime('%d.%m.%Y')
            
            url = f"{PRODUCTION_CALENDAR_BASE_URL}/get-period/{PRODUCTION_CALENDAR_TOKEN}/{country}/{date_str}/json"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Проверяем статус ответа
            if data.get('status') != 'ok':
                logger.warning(f"Production calendar API returned non-ok status: {data.get('status')}")
                # По умолчанию считаем будние дни рабочими
                return check_date.weekday() < 5
            
            # Ищем нужную дату в данных
            days = data.get('days', [])
            for day in days:
                if day.get('date') == date_str:
                    type_id = day.get('type_id')
                    # type_id: 1 - рабочий день, 2 - выходной, 3 - праздник, и т.д.
                    return type_id == 1
            
            # Если дата не найдена, используем стандартную логику (пн-пт рабочие)
            logger.warning(f"Date {date_str} not found in production calendar, using default logic")
            return check_date.weekday() < 5
            
        except Exception as e:
            logger.error(f"Error checking production calendar for date {check_date}: {e}")
            # В случае ошибки используем стандартную логику
            return check_date.weekday() < 5
    
    @staticmethod
    def get_period_info(start_date: date, end_date: date, country: str = 'ru') -> Dict:
        """
        Получает информацию о периоде из производственного календаря
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            country: Код страны
        
        Returns:
            Словарь с информацией о периоде
        """
        try:
            # Форматируем период в формат ДД.ММ.ГГГГ-ДД.ММ.ГГГГ
            start_str = start_date.strftime('%d.%m.%Y')
            end_str = end_date.strftime('%d.%m.%Y')
            period_str = f"{start_str}-{end_str}"
            
            url = f"{PRODUCTION_CALENDAR_BASE_URL}/get-period/{PRODUCTION_CALENDAR_TOKEN}/{country}/{period_str}/json"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'ok':
                logger.warning(f"Production calendar API returned non-ok status: {data.get('status')}")
                return {}
            
            return {
                'days': data.get('days', []),
                'statistic': data.get('statistic', {}),
                'country': data.get('country'),
                'period': data.get('period')
            }
            
        except Exception as e:
            logger.error(f"Error getting period info from production calendar: {e}")
            return {}
    
    @staticmethod
    def is_weekend(check_date: date, country: str = 'ru') -> bool:
        """
        Проверяет, является ли день выходным (по производственному календарю)
        
        Args:
            check_date: Дата для проверки
            country: Код страны
        
        Returns:
            True если выходной/праздничный день
        """
        return not ProductionCalendarService.is_working_day(check_date, country)
    
    @staticmethod
    def can_post_at_time(
        post_datetime: datetime,
        forbidden_hours_start: str = '22:00',
        forbidden_hours_end: str = '08:00',
        weekends_mode: str = 'disabled',
        use_production_calendar: bool = True,
        weekends_schedule: Optional[Dict] = None,
        country: str = 'ru'
    ) -> bool:
        """
        Проверяет, можно ли постить в указанное время с учетом всех правил
        
        Args:
            post_datetime: Дата и время постинга
            forbidden_hours_start: Начало запрещенного периода (формат HH:MM)
            forbidden_hours_end: Конец запрещенного периода (формат HH:MM)
            weekends_mode: Режим постинга в выходные ('disabled', 'weekday_schedule', 'custom')
            use_production_calendar: Использовать ли производственный календарь
            weekends_schedule: Расписание для выходных (если weekends_mode='custom')
            country: Код страны для производственного календаря
        
        Returns:
            True если можно постить, False если нельзя
        """
        post_date = post_datetime.date()
        post_time = post_datetime.time()
        
        # Проверяем запрещенные часы
        try:
            forbidden_start = datetime.strptime(forbidden_hours_start, '%H:%M').time()
            forbidden_end = datetime.strptime(forbidden_hours_end, '%H:%M').time()
            
            # Если запрещенный период переходит через полночь
            if forbidden_start > forbidden_end:
                # Например, 22:00 - 08:00
                if post_time >= forbidden_start or post_time < forbidden_end:
                    return False
            else:
                # Обычный период в пределах дня
                if forbidden_start <= post_time < forbidden_end:
                    return False
        except Exception as e:
            logger.error(f"Error parsing forbidden hours: {e}")
        
        # Проверяем выходные дни
        is_weekend_day = False
        if use_production_calendar:
            is_weekend_day = ProductionCalendarService.is_weekend(post_date, country)
        else:
            # Стандартная логика: суббота и воскресенье
            is_weekend_day = post_date.weekday() >= 5
        
        if is_weekend_day:
            if weekends_mode == 'disabled':
                return False
            elif weekends_mode == 'weekday_schedule':
                # Постим по расписанию будней (уже проверили запрещенные часы выше)
                return True
            elif weekends_mode == 'custom' and weekends_schedule:
                # Проверяем, попадает ли время в разрешенные для выходных
                allowed_times = weekends_schedule.get('times', [])
                post_time_str = post_time.strftime('%H:%M')
                return post_time_str in allowed_times
        
        # Для будних дней - можно постить (если не попадает в запрещенные часы)
        return True

