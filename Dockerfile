FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY main.py .
COPY .env.example .

# Создание директории для output
RUN mkdir -p /app/output

# Точка входа
ENTRYPOINT ["python", "main.py"]
CMD ["--output", "/app/output/translated_news.xml"]
