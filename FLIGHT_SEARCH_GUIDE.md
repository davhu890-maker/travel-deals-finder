# 🛫 Гайд по поиску дешевых перелетов

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install requests
```

### 2. Запуск простого поиска

#### Вариант А: Поиск из одного аэропорта в одно направление

```bash
python -c "
from flight_search_runner import FlightSearchRunner

# Инициализация с вашими ключами
runner = FlightSearchRunner(
    travelpayouts_token='a63fddaa09a757a60d85f48ced731dd7',
    aviasales_token='a63fddaa09a757a60d85f48ced731dd7',
    rapidapi_key='921753dbefmsh9b0467d9eddb199p154cc1jsndaad47aaf922'
)

# Поиск из Москвы в Стамбул
results = runner.search_from_russian_airports(
    destination='IST',  # Istanbul
    departure_date='2026-07-20',
    return_date='2026-07-27',
    airport_codes=['SVO']  # Только Шереметьево
)

for airport, flights in results.items():
    print(f'\n{airport}:')
    for flight in flights[:5]:
        print(f'  \${flight[\"price\"]} - {flight[\"source\"]} - {flight.get(\"airline\", \"N/A\")}')
"
```

#### Вариант Б: Поиск из всех московских аэропортов

```bash
python -c "
from flight_search_runner import FlightSearchRunner

runner = FlightSearchRunner(
    travelpayouts_token='a63fddaa09a757a60d85f48ced731dd7',
    aviasales_token='a63fddaa09a757a60d85f48ced731dd7',
    rapidapi_key='921753dbefmsh9b0467d9eddb199p154cc1jsndaad47aaf922'
)

# Поиск из всех московских аэропортов
results = runner.search_from_russian_airports(
    destination='BKK',  # Bangkok
    departure_date='2026-08-01',
    return_date='2026-08-15',
    airport_codes=['SVO', 'VKO', 'DME']  # Все московские аэропорты
)

for airport, flights in results.items():
    if flights:
        cheapest = flights[0]
        print(f'{airport}: \${cheapest[\"price\"]}')
"
```

### 3. Поиск дешевого перелета

```bash
python -c "
from flight_search_runner import FlightSearchRunner

runner = FlightSearchRunner(
    travelpayouts_token='a63fddaa09a757a60d85f48ced731dd7',
    aviasales_token='a63fddaa09a757a60d85f48ced731dd7',
    rapidapi_key='921753dbefmsh9b0467d9eddb199p154cc1jsndaad47aaf922'
)

# Найти САМЫЙ дешевый билет
cheapest = runner.find_cheapest_flight(
    departure_airports=['SVO', 'VKO', 'DME', 'AER', 'VOZ', 'ROV', 'KRR', 'MRV'],
    destination='IST',
    departure_date='2026-08-10',
    return_date='2026-08-20'
)

if cheapest:
    print(f'🎉 Найден дешевый билет!')
    print(f'Из: {cheapest[\"origin\"]}')
    print(f'В: {cheapest[\"destination\"]}')
    print(f'Цена: \${cheapest[\"price\"]}')
    print(f'Источник: {cheapest[\"source\"]}')
"
```

### 4. Поиск сложного маршрута с остановками

```bash
python -c "
from flight_search_runner import FlightSearchRunner

runner = FlightSearchRunner(
    travelpayouts_token='a63fddaa09a757a60d85f48ced731dd7',
    aviasales_token='a63fddaa09a757a60d85f48ced731dd7',
    rapidapi_key='921753dbefmsh9b0467d9eddb199p154cc1jsndaad47aaf922'
)

# Поиск с остановками (макс 7 дней или 21 день полета)
routes = runner.search_complex_routes(
    departure_airports=['SVO', 'VKO', 'DME'],
    destination='MAD',  # Madrid
    departure_date='2026-08-15',
    return_date='2026-09-05',
    max_stops=2,
    max_layover_hours=168,  # 7 дней максимум в пути
    max_total_duration_hours=504,  # 21 день максимум общая длительность
    budget=1500  # Не дороже 1500 долларов
)

print(f'Найдено маршрутов: {len(routes)}')
for route in routes[:5]:
    print(f'  \${route[\"price\"]} - {route[\"source\"]}')
"
```

### 5. Запуск полного поиска (сохранить в файл)

Создайте файл `search_flights.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полный поиск перелетов из всех русских аэропортов
"""
import json
from flight_search_runner import FlightSearchRunner
from datetime import datetime, timedelta

def main():
    # Инициализация
    runner = FlightSearchRunner(
        travelpayouts_token='a63fddaa09a757a60d85f48ced731dd7',
        aviasales_token='a63fddaa09a757a60d85f48ced731dd7',
        rapidapi_key='921753dbefmsh9b0467d9eddb199p154cc1jsndaad47aaf922'
    )
    
    # Параметры поиска
    destination = 'BKK'  # Bangkok
    departure_date = '2026-07-20'
    return_date = '2026-08-03'
    
    print("=" * 60)
    print(f"🌍 Поиск перелетов в {destination}")
    print(f"📅 {departure_date} → {return_date}")
    print("=" * 60)
    
    # 1. Поиск из всех русских аэропортов
    print("\n1️⃣ Поиск из всех русских аэропортов...")
    all_airports = runner.search_from_russian_airports(
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        airport_codes=['SVO', 'VKO', 'DME', 'AER', 'VOZ', 'ROV', 'KRR', 'MRV']
    )
    
    # Сортировка и вывод результатов
    results = []
    for airport, flights in all_airports.items():
        if flights:
            cheapest = flights[0]
            results.append({
                'airport': airport,
                'price': cheapest['price'],
                'source': cheapest['source'],
                'airline': cheapest.get('airline', 'N/A'),
                'stops': cheapest.get('stops', 0)
            })
    
    results.sort(key=lambda x: x['price'])
    
    print("\n📊 Результаты по аэропортам (от дешевого к дорогому):")
    for r in results:
        print(f"  {r['airport']}: ${r['price']} ({r['source']}) - {r['stops']} остановок")
    
    if results:
        best = results[0]
        print(f"\n🏆 ЛУЧШЕЕ ПРЕДЛОЖЕНИЕ: ${best['price']} из {best['airport']}")
    
    # 2. Поиск сложных маршрутов
    print("\n\n2️⃣ Поиск сложных маршрутов с остановками...")
    complex_routes = runner.search_complex_routes(
        departure_airports=['SVO', 'VKO', 'DME'],
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        budget=1200
    )
    
    print(f"Найдено маршрутов: {len(complex_routes)}")
    for i, route in enumerate(complex_routes[:5], 1):
        print(f"  {i}. ${route['price']} - {route['source']}")
    
    # 3. Сохранение результатов
    output = {
        'search_date': datetime.now().isoformat(),
        'destination': destination,
        'departure_date': departure_date,
        'return_date': return_date,
        'cheapest_flights': results,
        'complex_routes': complex_routes[:10]
    }
    
    with open('search_results.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Результаты сохранены в search_results.json")

if __name__ == '__main__':
    main()
```

Запуск:
```bash
python search_flights.py
```

## 📋 Доступные аэропорты

| Код | Город | Аэропорт |
|-----|-------|----------|
| SVO | Москва | Шереметьево |
| VKO | Москва | Внуково |
| DME | Москва | Домодедово |
| AER | Анапа | Анапа-Адлер |
| VOZ | Воронеж | Воронеж |
| ROV | Ростов-на-Дону | Ростов |
| KRR | Краснодар | Краснодар |
| MRV | Минеральные Воды | Минеральные Воды |

## 🗺️ Популярные направления

```python
# Азия
runner.find_cheapest_flight(['SVO'], 'BKK', '2026-07-20')  # Бангкок
runner.find_cheapest_flight(['SVO'], 'SGP', '2026-07-20')  # Сингапур
runner.find_cheapest_flight(['SVO'], 'HAN', '2026-07-20')  # Ханой

# Европа
runner.find_cheapest_flight(['SVO'], 'IST', '2026-07-20')  # Стамбул
runner.find_cheapest_flight(['SVO'], 'CDG', '2026-07-20')  # Париж
runner.find_cheapest_flight(['SVO'], 'BCN', '2026-07-20')  # Барселона

# Ближний Восток
runner.find_cheapest_flight(['SVO'], 'DXB', '2026-07-20')  # Дубай
runner.find_cheapest_flight(['SVO'], 'DOH', '2026-07-20')  # Доха
```

## ⚙️ Параметры поиска

### max_stops
- `0` - только прямые рейсы
- `1` - максимум 1 остановка
- `2` - максимум 2 остановки (по умолчанию)

### max_layover_hours
- `48` - макс 2 дня в пути
- `168` - макс 7 дней в пути (по умолчанию)
- `504` - макс 21 день в пути

### budget
Максимальная цена в USD

## 🔍 Примеры сложных запросов

### Поиск дешевых выходных
```python
runner.search_from_russian_airports(
    destination='IST',
    departure_date='2026-07-20',
    return_date='2026-07-22',  # 2 дня
    airport_codes=['SVO', 'VKO', 'DME']
)
```

### Поиск недели
```python
runner.search_from_russian_airports(
    destination='BKK',
    departure_date='2026-08-01',
    return_date='2026-08-08',  # 7 дней
    airport_codes=['SVO']
)
```

### Поиск с бюджетом
```python
runner.search_complex_routes(
    departure_airports=['SVO', 'VKO', 'DME'],
    destination='MAD',
    departure_date='2026-09-01',
    return_date='2026-09-15',
    budget=1500  # Не дороже 1500 долларов
)
```

## 📊 Интерпретация результатов

```json
{
  "price": 450,
  "origin": "SVO",
  "destination": "BKK",
  "departure_date": "2026-07-20",
  "return_date": "2026-08-03",
  "airline": "Turkish Airlines",
  "stops": 1,
  "source": "TravelPayouts",
  "url": "https://..."
}
```

- **price** - цена в USD
- **origin** - аэропорт вылета
- **destination** - аэропорт прилета
- **stops** - количество пересадок
- **source** - откуда найден билет
- **url** - ссылка на бронирование

## ⚡ Советы и трюки

### Быстрый поиск
Ищите в середине недели (вт-чт), обычно дешевле

### Гибкие даты
Попробуйте разные даты плюс-минус неделю

### Из разных аэропортов
Иногда из провинциальных аэропортов (AER, KRR) дешевле

### Сложные маршруты
Полеты с остановками часто дешевле прямых

## 🐛 Решение проблем

### Ошибка: "Connection timeout"
```bash
# Проверьте интернет и попробуйте позже
python search_flights.py
```

### Ошибка: "401 Unauthorized"
Проверьте правильность API ключей в коде

### Нет результатов
- Убедитесь, что дата вылета в будущем
- Проверьте код аэропорта (должен быть 3 буквы)
- Попробуйте другую дату

### Результаты только от одного источника
Это нормально, не все API работают одинаково. Ищите в разные дни.

## 📞 Поддержка

Если возникают проблемы:
1. Проверьте логи в консоли (будут ошибки на английском)
2. Убедитесь, что установлены зависимости: `pip install requests`
3. Проверьте API ключи в `config_flights.json`

Удачного поиска! ✈️
