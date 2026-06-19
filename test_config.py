#!/usr/bin/env python3
"""
Скрипт для тестирования конфигурации и подключения к API
"""

import json
import logging
import asyncio
from main import TravelDealsFinder

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_config():
    """Тест конфигурации"""
    print("\n=== Тест конфигурации ===")
    try:
        finder = TravelDealsFinder('config.json')
        config = finder.config
        
        print("✓ Конфигурация загружена успешно")
        print(f"  - Точек отправления: {len(config.get('departure_points', []))}")
        print(f"  - Направлений: {len(config.get('destinations', []))}")
        print(f"  - Интервал поиска: {config.get('search_interval_minutes')} минут")
        print(f"  - Минимальная скидка: {config.get('min_discount')}%")
        
        # Проверка API ключей
        print("\n  API ключи:")
        if config.get('kayak', {}).get('api_key') and config['kayak']['api_key'] != 'your_kayak_api_key_here':
            print("  ✓ Kayak API ключ установлен")
        else:
            print("  ✗ Kayak API ключ не установлен")
        
        if config.get('skyscanner', {}).get('api_key') and config['skyscanner']['api_key'] != 'your_skyscanner_api_key_here':
            print("  ✓ SkyScanner API ключ установлен")
        else:
            print("  ✗ SkyScanner API ключ не установлен")
        
        # Проверка уведомлений
        print("\n  Каналы уведомлений:")
        if config.get('email', {}).get('sender') and config['email']['sender'] != 'your_email@gmail.com':
            print("  ✓ Email настроен")
        else:
            print("  ✗ Email не настроен")
        
        if config.get('telegram', {}).get('token') and config['telegram']['token'] != 'your_telegram_bot_token':
            print("  ✓ Telegram настроен")
        else:
            print("  ✗ Telegram не настроен")
        
        if config.get('slack', {}).get('webhook_url') and config['slack']['webhook_url'] != 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL':
            print("  ✓ Slack настроен")
        else:
            print("  ✗ Slack не настроен")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка конфигурации: {e}")
        return False

async def test_apis():
    """Тест подключения к API"""
    print("\n=== Тест API подключений ===")
    try:
        finder = TravelDealsFinder('config.json')
        
        if not finder.flight_apis:
            print("⚠ Ни один API не настроен. Пожалуйста, установите API ключи в config.json")
            return False
        
        print(f"✓ Найдено {len(finder.flight_apis)} API(ев)")
        
        # Тестовый поиск
        print("\nПопытка тестового поиска...")
        deals = await finder.search_all_deals()
        print(f"✓ Поиск выполнен, найдено {len(deals)} предложений")
        
        if deals:
            print(f"\nПример предложения:")
            deal = deals[0]
            print(f"  {deal.departure_city} → {deal.destination_city}")
            print(f"  Цена: ${deal.price} {deal.currency}")
            print(f"  Дата: {deal.departure_date}")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка API: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_notifications():
    """Тест системы уведомлений"""
    print("\n=== Тест системы уведомлений ===")
    try:
        from main import NotificationService, Deal
        finder = TravelDealsFinder('config.json')
        notifier = finder.notifier
        
        # Создаем тестовое предложение
        test_deal = Deal(
            departure_city="Москва",
            departure_code="MOW",
            destination_city="Таиланд",
            destination_code="BKK",
            price=450,
            currency="USD",
            departure_date="2026-07-15",
            return_date="2026-07-22",
            airline="S7",
            deal_type="flight",
            url="https://example.com/booking",
            discount_percent=25
        )
        
        print("Попытка отправки тестовых уведомлений...")
        notifier.send_email([test_deal])
        print("✓ Email попытка отправки (проверьте логи)")
        
        notifier.send_telegram([test_deal])
        print("✓ Telegram попытка отправки (проверьте логи)")
        
        notifier.send_slack([test_deal])
        print("✓ Slack попытка отправки (проверьте логи)")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка уведомлений: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Главная функция тестирования"""
    print("""╔═══════════════════════════════════════╗
║  Travel Deals Finder - Тест конфигурации  ║
╚═══════════════════════════════════════╝""")
    
    # Тест конфигурации
    config_ok = test_config()
    
    # Тест API
    if config_ok:
        api_ok = await test_apis()
    else:
        api_ok = False
    
    # Тест уведомлений
    if config_ok:
        notify_ok = test_notifications()
    else:
        notify_ok = False
    
    # Итоги
    print("\n=== Итоги тестирования ===")
    print(f"Конфигурация: {'✓' if config_ok else '✗'}")
    print(f"API подключение: {'✓' if api_ok else '✗'}")
    print(f"Уведомления: {'✓' if notify_ok else '✗'}")
    
    if config_ok and api_ok and notify_ok:
        print("\n✓ Все тесты пройдены! Приложение готово к работе.")
    else:
        print("\n✗ Некоторые тесты не прошли. Пожалуйста, проверьте конфигурацию.")

if __name__ == '__main__':
    asyncio.run(main())
