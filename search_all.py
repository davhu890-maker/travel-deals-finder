#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛫 Полный поиск дешевых перелетов во ВСЕ направления
из ВСЕХ русских аэропортов
"""
import sys
import json
from datetime import datetime, timedelta
from itertools import product

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

# Популярные направления
POPULAR_DESTINATIONS = {
    # Азия
    "BKK": "Bangkok, Thailand",
    "SGP": "Singapore",
    "HAN": "Hanoi, Vietnam",
    "HCM": "Ho Chi Minh City, Vietnam",
    "KUL": "Kuala Lumpur, Malaysia",
    "PYE": "Phuket, Thailand",
    
    # Европа
    "IST": "Istanbul, Turkey",
    "CDG": "Paris, France",
    "BCN": "Barcelona, Spain",
    "MAD": "Madrid, Spain",
    "LHR": "London, UK",
    "AMS": "Amsterdam, Netherlands",
    "PRG": "Prague, Czech Republic",
    "BUD": "Budapest, Hungary",
    
    # Ближний Восток
    "DXB": "Dubai, UAE",
    "DOH": "Doha, Qatar",
    "AUH": "Abu Dhabi, UAE",
    
    # Северная Африка
    "CAI": "Cairo, Egypt",
    "HRG": "Hurghada, Egypt",
    
    # Центральная Азия
    "TSE": "Astana, Kazakhstan",
    "ALA": "Almaty, Kazakhstan",
    "TAS": "Tashkent, Uzbekistan",
}

def search_direct(origin, destination, departure_date, return_date=None):
    """Поиск прямых перелетов"""
    try:
        from search_engines import TravelPayoutsSearcher, AviasalesSearcher, SkyScannerSearcher
        
        searchers = {
            "TravelPayouts": TravelPayoutsSearcher(TRAVELPAYOUTS_TOKEN) if TRAVELPAYOUTS_TOKEN else None,
            "Aviasales": AviasalesSearcher(AVIASALES_TOKEN) if AVIASALES_TOKEN else None,
            "SkyScanner": SkyScannerSearcher(RAPIDAPI_KEY) if RAPIDAPI_KEY else None,
        }
        
        all_flights = []
        
        # Поиск через все источники
        if searchers["TravelPayouts"]:
            try:
                flights = searchers["TravelPayouts"].search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date
                )
                all_flights.extend(flights)
            except:
                pass
        
        if searchers["Aviasales"]:
            try:
                flights = searchers["Aviasales"].search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date
                )
                all_flights.extend(flights)
            except:
                pass
        
        if searchers["SkyScanner"]:
            try:
                flights = searchers["SkyScanner"].search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date
                )
                all_flights.extend(flights)
            except:
                pass
        
        if not all_flights:
            return None
        
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
        
        # Возвращаем самый дешевый
        if unique:
            unique.sort(key=lambda x: x.get("price", float("inf")))
            return unique[0]
        
        return None
    
    except:
        return None


def scan_all_directions(departure_date, return_date=None, max_price=None):
    """Сканирование всех направлений из всех аэропортов"""
    print("\n" + "="*100)
    print("🌍 ПОЛНЫЙ ПОИСК: ВСЕ АЭРОПОРТЫ → ВСЕ НАПРАВЛЕНИЯ")
    print("="*100)
    print(f"📅 Вылет: {departure_date}", end="")
    if return_date:
        print(f" | Возврат: {return_date}")
    else:
        print(" (в одну сторону)")
    if max_price:
        print(f"💰 Максимальная цена: ${max_price}")
    print("="*100)
    
    results = []
    total_combinations = len(RUSSIAN_AIRPORTS) * len(POPULAR_DESTINATIONS)
    current = 0
    
    for origin_code, origin_name in RUSSIAN_AIRPORTS.items():
        for dest_code, dest_name in POPULAR_DESTINATIONS.items():
            current += 1
            percent = (current / total_combinations) * 100
            
            print(f"\r[{current:3d}/{total_combinations}] {percent:5.1f}% | {origin_code} → {dest_code}", end="", flush=True)
            
            flight = search_direct(origin_code, dest_code, departure_date, return_date)
            
            if flight:
                price = flight.get("price", float("inf"))
                
                # Фильтр по цене
                if max_price and price > max_price:
                    continue
                
                results.append({
                    'origin': origin_code,
                    'origin_name': origin_name,
                    'destination': dest_code,
                    'dest_name': dest_name,
                    'price': price,
                    'source': flight.get('source'),
                    'airline': flight.get('airline', 'N/A'),
                    'stops': flight.get('stops', 0),
                    'url': flight.get('url', '')
                })
    
    print("\n")
    
    if not results:
        print("❌ Результатов не найдено")
        return []
    
    # Сортировка по цене
    results.sort(key=lambda x: x['price'])
    
    return results


def print_results_table(results, limit=50):
    """Вывод результатов в виде таблицы"""
    print("\n" + "="*120)
    print("✅ НАЙДЕНО ДЕШЕВЫХ ПЕРЕЛЕТОВ")
    print("="*120)
    print(f"{'ИЗ':<15} {'В':<20} {'ЦЕНА':<10} {'ИСТОЧНИК':<15} {'АВИАЛИНИЯ':<20} {'ОСТАНОВОК':<10}")
    print("-"*120)
    
    for i, result in enumerate(results[:limit]):
        print(f"{result['origin']:<15} {result['dest_name'][:19]:<20} ${result['price']:<9.0f} {result['source']:<15} {result['airline'][:19]:<20} {result['stops']:<10}")
    
    if len(results) > limit:
        print(f"\n... и еще {len(results) - limit} предложений")
    
    print("="*120)


def print_summary(results):
    """Сводка по результатам"""
    print("\n📊 СТАТИСТИКА:")
    print("-"*50)
    
    # Группировка по аэропортам вылета
    from_airports = {}
    for r in results:
        origin = r['origin']
        if origin not in from_airports:
            from_airports[origin] = []
        from_airports[origin].append(r)
    
    print("\n🔸 ПО АЭРОПОРТАМ ВЫЛЕТА (минимальная цена):")
    for airport in sorted(RUSSIAN_AIRPORTS.keys()):
        if airport in from_airports:
            min_price = min(r['price'] for r in from_airports[airport])
            dest_name = next((r['dest_name'] for r in from_airports[airport] if r['price'] == min_price), 'N/A')
            print(f"  {airport}: ${min_price:.0f} ({dest_name})")
    
    # Группировка по направлениям
    destinations = {}
    for r in results:
        dest = r['destination']
        if dest not in destinations:
            destinations[dest] = []
        destinations[dest].append(r)
    
    print("\n🔸 ПО НАПРАВЛЕНИЯМ (минимальная цена):")
    for dest_code in sorted(POPULAR_DESTINATIONS.keys()):
        if dest_code in destinations:
            min_price = min(r['price'] for r in destinations[dest_code])
            from_airport = next((r['origin'] for r in destinations[dest_code] if r['price'] == min_price), 'N/A')
            dest_name = POPULAR_DESTINATIONS[dest_code]
            print(f"  {dest_code} ({dest_name}): ${min_price:.0f} из {from_airport}")
    
    # Источники
    sources = {}
    for r in results:
        src = r['source']
        sources[src] = sources.get(src, 0) + 1
    
    print("\n🔸 ПО ИСТОЧНИКАМ:")
    for src, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        print(f"  {src}: {count} предложений")
    
    print(f"\n🏆 ЛУЧШЕЕ ПРЕДЛОЖЕНИЕ: ${results[0]['price']:.0f}")
    print(f"   {results[0]['origin']} → {results[0]['dest_name']}")
    print(f"   Источник: {results[0]['source']}")


def save_results(results, filename="search_results.json"):
    """Сохранение результатов в JSON"""
    output = {
        'search_date': datetime.now().isoformat(),
        'total_results': len(results),
        'results': results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Результаты сохранены в {filename}")


def main():
    """Главное меню"""
    print("\n" + "="*100)
    print("✈️  ПОЛНЫЙ ПОИСК ДЕШЕВЫХ ПЕРЕЛЕТОВ")
    print("="*100)
    
    # Параметры поиска
    if len(sys.argv) > 1:
        departure_date = sys.argv[1]
        return_date = sys.argv[2] if len(sys.argv) > 2 else None
        max_price = int(sys.argv[3]) if len(sys.argv) > 3 else None
    else:
        # По умолчанию - через неделю, на 2 недели
        today = datetime.now()
        departure_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        return_date = (today + timedelta(days=21)).strftime("%Y-%m-%d")
        max_price = None
        
        print(f"\n⚠️  Параметры не указаны, используются значения по умолчанию:")
        print(f"   Вылет: {departure_date}")
        print(f"   Возврат: {return_date}")
        print(f"\nДля своих параметров используйте:")
        print(f"   python search_all.py 2026-07-20 2026-08-03")
        print(f"   python search_all.py 2026-08-01 2026-08-15 1500")
    
    # Сканирование
    results = scan_all_directions(departure_date, return_date, max_price)
    
    if results:
        # Вывод
        print_results_table(results, limit=30)
        print_summary(results)
        save_results(results)
        
        print("\n✅ Поиск завершен успешно!")
    else:
        print("\n❌ Результатов не найдено")


if __name__ == '__main__':
    main()
