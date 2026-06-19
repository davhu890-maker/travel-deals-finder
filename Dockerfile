FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование файлов приложения
COPY main.py .
COPY config.json .

# Создание директории для логов
RUN mkdir -p /app/logs

# Запуск приложения
CMD ["python", "main.py"]
