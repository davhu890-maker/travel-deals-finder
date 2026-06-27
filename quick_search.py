#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛫 Простой скрипт для поиска дешевых перелетов
Без зависимостей от Kayak - используем TravelPayouts, Aviasales, SkyScanner
"""
import sys
import json
from datetime import datetime, timedelta

# Ваши API ключи
TRAVELPAYOUTS_TOKEN = "a63fddaa09a757a60d85f48ced731dd7"
AVIASALES_TOKEN = "a63fddaa09a757a60d85f48ced731dd7"
RAPIDAPI_KEY = "921753dbefmsh9b0467d9eddb199p154cc1jsndaad47aaf922"

# Русские аэропорты
RUSSIAN_AIRPORTS = {
    "SVO": "Sheremetyevo (Москва)",
    "VKO": "Vnukovo (Москва)",
    "DME": "Domodedovo (Москва)",
    "AER": "Anapa",
    "VOZ": "Voronezh",
    "ROV": "Rostov-on-Don",
    "KRR": "Krasnodar",
    "MRV": "Mineralnye Vody"
}

def search_direct(origin, destination, departure_date, return_date=None):
    """Поиск прямых перелетов"""
    print(f"\n{'='*70}")
    print(f"🔍 Поиск: {origin} → {destination}")
    print(f"📅 {departure_date}", end="")
    if return_date:
        print(f" (возврат {return_date})")
    else:
        print(" (в одну сторону)")
    print(f"{'='*70}")
    
    try:
        from search_engines import TravelPayoutsSearcher, AviasalesSearcher, SkyScannerSearcher
        
        searchers = {
            "TravelPayouts": TravelPayoutsSearcher(TRAVELPAYOUTS_TOKEN) if TRAVELPAYOUTS_TOKEN else None,
            "Aviasales": AviasalesSearcher(AVIASALES_TOKEN) if AVIASALES_TOKEN else None,
            "SkyScanner": SkyScannerSearcher(RAPIDAPI_KEY) if RAPIDAPI_KEY else None,
        }
        
        all_flights = []
        
        # Поиск через TravelPayouts
        if searchers["TravelPayouts"]:
            try:
                print("📡 Поиск через TravelPayouts...", end=" ", flush=True)
                flights = searchers["TravelPayouts"].search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date
                )
                print(f"✓ найдено {len(flights)}")
                all_flights.extend(flights)
            except Exception as e:
                print(f"✗ ошибка: {str(e)[:50]}")
        
        # Поиск через Aviasales
        if searchers["Aviasales"]:
            try:
                print("📡 Поиск через Aviasales...", end=" ", flush=True)
                flights = searchers["Aviasales"].search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date
                )
                print(f"✓ найдено {len(flights)}")
                all_flights.extend(flights)
            except Exception as e:
                print(f"✗ ошибка: {str(e)[:50]}")
        
        # Поиск через SkyScanner
        if searchers["SkyScanner"]:
            try:
                print("📡 Поиск через SkyScanner...", end=" ", flush=True)
                flights = searchers["SkyScanner"].search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date
                )
                print(f"✓ найдено {len(flights)}")
                all_flights.extend(flights)
            except Exception as e:
                print(f"✗ ошибка: {str(e)[:50]}")
        
        if not all_flights:
            print("❌ Результатов не найдено")
            return []
        
        # Удаление дубликатов
        seen = set()
        unique = []
        for flight in all_flights:
            key = (
                flight.get("origin"),
                flight.get("destination"),
                flight.get("departure_date"),
                round(float(flight.get("price", 0)))
            )
            if key not in seen:
                seen.add(key)
                unique.append(flight)
        
        # Сортировка по цене
        unique.sort(key=lambda x: x.get("price", float("inf")))
        
        # Вывод результатов
        print(f"\n✅ Всего уникальных предложений: {len(unique)}")
        print(f"\n{'Цена':<10} {'Источник':<15} {'Авиалиния':<20} {'Остановок':<10}")
        print("-" * 55)
        
        for i, flight in enumerate(unique[:10]):
            price = flight.get("price", "N/A")
            source = flight.get("source", "N/A")[:14]
            airline = flight.get("airline", "N/A")[:19]
            stops = flight.get("stops", 0)
            print(f"${price:<9} {source:<15} {airline:<20} {stops:<10}")
        
        if len(unique) > 10:
            print(f"... и еще {len(unique) - 10} предложений")
        
        return unique
    
    except ImportError:
        print("❌ Ошибка: не установлены модули поиска")
        print("Убедитесь, что файлы в папке search_engines/ существуют")
        return []
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return []


def search_from_all_airports(destination, departure_date, return_date=None):
    """Поиск из всех русских аэропортов"""
    print(f"\n{'='*70}")
    print(f"🌍 ПОИСК ИЗ ВСЕХ РУССКИХ АЭРОПОРТОВ")
    print(f"Направление: {destination}")
    print(f"{'='*70}")
    
    results = {}
    
    for airport_code in RUSSIAN_AIRPORTS.keys():
        flights = search_direct(airport_code, destination, departure_date, return_date)
        results[airport_code] = flights
    
    # Сводка по аэропортам
    print(f"\n\n{'='*70}")
    print("📊 СВОДКА ПО АЭРОПОРТАМ (от дешевого к дорогому)")
    print(f"{'='*70}")
    print(f"{'Аэропорт':<15} {'Цена':<10} {'Источник':<15} {'Остановок'}")
    print("-" * 55)
    
    summary = []
    for airport_code, flights in results.items():
        if flights:
            cheapest = flights[0]
            summary.append({
                'airport': airport_code,
                'name': RUSSIAN_AIRPORTS[airport_code],
                'price': cheapest['price'],
                'source': cheapest['source'],
                'stops': cheapest.get('stops', 0)
            })
    
    summary.sort(key=lambda x: x['price'])
    
    for item in summary:
        print(f"{item['airport']:<15} ${item['price']:<9} {item['source']:<15} {item['stops']}")
    
    if summary:
        best = summary[0]
        print(f"\n🏆 ЛУЧШЕЕ ПРЕДЛОЖЕНИЕ: ${best['price']} из {best['airport']} ({best['name']})")
    
    return results


def main():
    """Главное меню"""
    print("\n" + "="*70)
    print("✈️  ПОИСК ДЕШЕВЫХ ПЕРЕЛЕТОВ ИЗ РОССИИ")
    print("="*70)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "all":
            # python quick_search.py all BKK 2026-07-20 2026-08-03
            if len(sys.argv) >= 4:
                destination = sys.argv[2]
                departure_date = sys.argv[3]
                return_date = sys.argv[4] if len(sys.argv) > 4 else None
                search_from_all_airports(destination, departure_date, return_date)
        
        elif command == "search":
            # python quick_search.py search SVO BKK 2026-07-20 2026-08-03
            if len(sys.argv) >= 5:
                origin = sys.argv[2]
                destination = sys.argv[3]
                departure_date = sys.argv[4]
                return_date = sys.argv[5] if len(sys.argv) > 5 else None
                search_direct(origin, destination, departure_date, return_date)
        
        else:
            print_help()
    else:
        print_help()


def print_help():
    """Справка"""
    print("\n📖 СПРАВКА:\n")
    print("1️⃣  Поиск из всех русских аэропортов:")
    print("   python quick_search.py all BKK 2026-07-20 2026-08-03")
    print("   python quick_search.py all IST 2026-07-20")
    print("\n2️⃣  Поиск из конкретного аэропорта:")
    print("   python quick_search.py search SVO BKK 2026-07-20 2026-08-03")
    print("   python quick_search.py search VKO IST 2026-08-01")
    
    print("\n📍 Доступные аэропорты:")
    for code, name in sorted(RUSSIAN_AIRPORTS.items()):
        print(f"   {code} - {name}")
    
    print("\n🌍 Популярные направления:")
    print("   BKK - Bangkok, Thailand")
    print("   IST - Istanbul, Turkey")
    print("   DXB - Dubai, UAE")
    print("   CDG - Paris, France")
    print("   BCN - Barcelona, Spain")
    print("   SGP - Singapore")
    print("   DOH - Doha, Qatar")
    print("   MAD - Madrid, Spain")
    
    print("\n💡 Примеры:")
    print("   # Дешевый выходной в Стамбул")
    print("   python quick_search.py all IST 2026-07-19 2026-07-21")
    print()
    print("   # Неделя в Бангкоке")
    print("   python quick_search.py all BKK 2026-08-01 2026-08-08")
    print()
    print("   # Из Домодедова в Дубай")
    print("   python quick_search.py search DME DXB 2026-09-01 2026-09-10")
    print()


if __name__ == '__main__':
    main()
