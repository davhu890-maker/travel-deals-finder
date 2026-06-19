# 🌍 Travel Hot Deals Finder

Автоматический скрипт для поиска выгодных туров и перелетов из нескольких точек отправления с периодическими уведомлениями.

## ✨ Возможности

- 🔍 **Поиск из нескольких городов** - задайте несколько точек отправления
- 🌎 **Множество направлений** - ищите туры в разные страны одновременно
- 💰 **Выгодные предложения** - фильтрация по минимальной скидке и максимальной цене
- 📧 **Email уведомления** - красивые письма с найденными предложениями
- 📱 **Telegram боты** - получайте уведомления в мессенджер
- 💬 **Slack интеграция** - делитесь находками с командой
- 🤖 **Автоматизация** - периодический поиск с настраиваемым интервалом
- 💾 **История предложений** - не получай��е повторные уведомления

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка конфигурации

Отредактируйте `config.json`:

```json
{
  "departure_points": [
    {"name": "Москва", "code": "MOW"},
    {"name": "СПб", "code": "LED"}
  ],
  "destinations": [
    {"name": "Таиланд", "code": "BKK"},
    {"name": "Турция", "code": "IST"}
  ],
  "search_interval_minutes": 60,
  "min_discount": 15,
  "max_prices": {
    "BKK": 800,
    "IST": 600
  }
}
```

### 3. Получение API ключей

#### Kayak API
1. Перейдите на https://www.kayak.com/dev
2. Зарегистрируйте приложение
3. Получите API ключ

#### SkyScanner API
1. Перейдите на https://rapidapi.com/skyscanner/api/skyscanner-flight-search
2. Подпишитесь на API
3. Получите ключ

#### Tour Operator API
- Замените на реальный API вашего туроператора

### 4. Настройка Email

#### Gmail (рекомендуется)
1. Включите двухфакторную аутентификацию на аккаунте Gmail
2. Сгенерируйте пароль приложения: https://myaccount.google.com/apppasswords
3. Используйте этот пароль в конфигурации

### 5. Настройка Telegram (опционально)

1. Создайте бота через @BotFather в Telegram
2. Получите токен
3. Найдите ваш Chat ID, отправив боту любое сообщение
4. Используйте @userinfobot для получения Chat ID

### 6. Настройка Slack (опционально)

1. Создайте Webhook: https://api.slack.com/messaging/webhooks
2. Скопируйте URL webhook'а в конфигурацию

## 📋 Использование

### Однократный поиск

```bash
RUN_ONCE=true python main.py
```

### Периодический поиск (каждый час)

```bash
SEARCH_INTERVAL_MINUTES=60 python main.py
```

### Запуск в фоне (Linux/Mac)

```bash
nohup python main.py &
```

### Запуск как сервис systemd (Linux)

Создайте файл `/etc/systemd/system/travel-deals.service`:

```ini
[Unit]
Description=Travel Hot Deals Finder
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/travel-deals-finder
ExecStart=/usr/bin/python3 /path/to/travel-deals-finder/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запустите:
```bash
sudo systemctl start travel-deals
sudo systemctl enable travel-deals
```

### Docker контейнер

Создайте `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .
COPY config.json .

CMD ["python", "main.py"]
```

Запустите:
```bash
docker build -t travel-deals .
docker run -it travel-deals
```

## ⚙️ Конфигурация

### Основные параметры

- `departure_points` - список городов отправления (код IATA)
- `destinations` - список направлений (код IATA)
- `search_interval_minutes` - интервал поиска в минутах
- `search_date` - дата вылета (формат YYYY-MM-DD)
- `return_date` - дата возврата (опционально)
- `tour_nights` - количество ночей для туров

### Фильтры

- `min_discount` - минимальная скидка в процентах
- `max_prices` - максимальная цена по направлениям

### Уведомления

- `email` - Email уведомления
- `telegram` - Telegram боты
- `slack` - Slack интеграция

## 🌐 Коды IATA аэропортов

- MOW - Москва (Домодедово, Шереметьево, Внуково)
- LED - Санкт-Петербург
- KZN - Казань
- BKK - Бангкок, Таиланд
- IST - Стамбул, Турция
- CAI - Каир, Египет
- DXB - Дубай, ОАЭ
- MAD - Мадрид, Испания
- CDG - Париж
- LHR - Лондон

[Полный список IATA кодов](https://www.iata.org/publications/directories/code-search/)

## 📊 Пример выходных данных

### Email

Красивое письмо с таблицей найденных предложений, включающей:
- Маршрут (откуда → куда)
- Цену в USD
- Процент скидки
- Дату вылета
- Тип (рейс или тур)
- Прямую ссылку на бронирование

### Telegram

```
🎉 Найдены выгодные туры и перелеты!

1. Москва → Таиланд
💰 Цена: $450 USD
📉 Скидка: 25%
📅 Дата: 2026-07-15
✈️ Тип: flight
🔗 Смотреть предложение
```

### Slack

Интерактивные сообщения с кнопками "Посмотреть"

## 🐛 Решение проблем

### Ошибка: "Config file not found"

```bash
cp config.json.example config.json
```

### Email не отправляется

- Проверьте пароль приложения Gmail
- Убедитесь, что email_recipients - это список
- Проверьте логи: `cat travel_deals.log`

### API возвращают пустой результат

- Проверьте корректность кодов IATA
- Убедитесь, что дата вылета в будущем
- Проверьте лимиты API

## 📝 Логи

Все события сохраняются в `travel_deals.log`:

```
2026-06-19 10:00:00 - root - INFO - Starting travel deals search...
2026-06-19 10:00:05 - root - INFO - Found 150 total deals
2026-06-19 10:00:06 - root - INFO - Found 12 good deals
2026-06-19 10:00:07 - root - INFO - Email sent to recipient@example.com
```

## 🔒 Безопасность

- Никогда не коммитьте `config.json` с реальными ключами
- Используйте `.env` файл для чувствительных данных
- Ограничьте доступ к файлам конфигурации
- Используйте app passwords вместо главного пароля

## 📈 Рекомендации

1. **Оптимальный интервал** - 2-4 часа для лучшего баланса между актуальностью и нагрузкой
2. **Отключение каналов** - закомментируйте ненужные методы отправки в `run_search()`
3. **Тестирование** - используйте `RUN_ONCE=true` для проверки конфигурации
4. **Мониторинг** - регулярно проверяйте логи

## 📄 Лицензия

MIT License

## 🤝 Помощь

Если возникли проблемы:
1. Проверьте `travel_deals.log`
2. Убедитесь, что все API ключи верны
3. Проверьте подключение к интернету
4. Создайте issue с логами ошибок

## 🚀 Планы развития

- [ ] Веб-интерфейс для управления
- [ ] Поддержка дополнительных API
- [ ] Предварительные уведомления перед падением цены
- [ ] Сравнение цен в разных валютах
- [ ] Интеграция с календарём Google
- [ ] Push-уведомления в мобильное приложение

---

**Созданого с ❤️ для путешественников**
