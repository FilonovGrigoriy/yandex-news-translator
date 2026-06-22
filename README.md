<div align="center">

# 📰 News Parser & Translator

**Автоматический сбор, перевод и генерация RSS-лент новостей**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style](https://img.shields.io/badge/Code%20style-PEP%208-black)](https://peps.python.org/pep-0008/)
[![CI](https://github.com/FilonovGrigoriy/yandex-news-translator/actions/workflows/ci.yml/badge.svg)](https://github.com/FilonovGrigoriy/yandex-news-translator/actions)
[![Yandex Cloud](https://img.shields.io/badge/Yandex%20Cloud-Translate%20API-red?logo=yandex)](https://cloud.yandex.ru/)

</div>

---

## 📑 Оглавление

- [О проекте](#-о-проекте)
- [Возможности](#-возможности)
- [Архитектура](#-архитектура)
- [Быстрый старт](#-быстрый-старт)
- [Установка](#-установка)
- [Настройка](#-настройка)
- [Использование](#-использование)
- [Пример вывода](#-пример-вывода)
- [Переменные окружения](#-переменные-окружения)
- [Roadmap](#-roadmap)
- [Лицензия](#-лицензия)

---

## 🎯 О проекте

**News Parser & Translator** — это production-ready CLI-инструмент, который:

1. 🕷️ **Собирает** последние новости из любого RSS-источника
2. 🌐 **Переводит** заголовки и описания на английский язык через **Yandex Cloud Translate API**
3. 📡 **Генерирует** валидную RSS-ленту (`translated_news.xml`) для дальнейшего использования

Идеально подходит для создания мультиязычных агрегаторов новостей, Telegram-ботов или интеграции с CMS.

---

## ✨ Возможности

| Фича | Описание |
|------|----------|
| ⚡ **Батчевый перевод** | Все тексты отправляются одним запросом — экономия времени и денег |
| 🗃️ **Smart Cache** | SHA256-кэш переводов в JSON. Повторные тексты не тарифицируются |
| 🔄 **Auto Retry** | Exponential backoff при `429/500/502/503/504` |
| 🧹 **HTML Sanitizer** | Автоматическая очистка HTML-тегов и декодирование сущностей |
| 📅 **Smart Dates** | Многоуровневый fallback для парсинга дат из RSS |
| 🎛️ **CLI** | Аргументы командной строки для переопределения любой настройки |
| 🛑 **Graceful Shutdown** | Корректная обработка `Ctrl+C` без потери данных |
| 📐 **PEP 8** | Type hints, docstrings, dataclasses, чистая архитектура |

---

## 🏗️ Архитектура

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   RSS Source    │────▶│  fetch_news()   │────▶│  NewsItem[]     │
│ (Lenta, Habr...)│     │  feedparser     │     │  title,summary  │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                       │
                              ┌────────────────────────┘
                              ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Yandex Cloud   │◀────│ translate_items │◀────│  Translation    │
│  Translate API  │     │  (batch + cache)│     │  Cache (JSON)   │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ translated_news │◀────│  generate_rss() │
│    .xml         │     │    feedgen      │
└─────────────────┘     └─────────────────┘
```

### Стек технологий

- **Python 3.10+**
- `feedparser` — парсинг RSS/Atom
- `feedgen` — генерация валидного RSS 2.0
- `requests` + `urllib3.Retry` — HTTP с автоматическим retry
- `python-dotenv` — управление конфигурацией

---

## 🚀 Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone https://github.com/FilonovGrigoriy/yandex-news-translator.git
cd yandex-news-translator

# 2. Создать окружение
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить переменные окружения
cp .env.example .env
# Отредактируй .env, добавив API-ключ Yandex

# 5. Запустить
python main.py
```

---

## 🛠️ Установка

### Требования

- Python **3.10** или выше
- Аккаунт [Yandex Cloud](https://cloud.yandex.ru/) с активированным **Translate API**

### Шаги

```bash
# Создание виртуального окружения
python -m venv venv

# Активация
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate.bat      # Windows CMD
venv\Scripts\Activate.ps1     # Windows PowerShell

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ Настройка

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
```

### Получение Yandex API Key

1. Перейдите в [Yandex Cloud Console](https://console.cloud.yandex.ru/)
2. Создайте **сервисный аккаунт**
3. Сгенерируйте **API-ключ** (не IAM-токен!)
4. Узнайте **Folder ID** в настройках каталога
5. Назначьте роль `ai.translate.user` или `editor`

### Файл `.env`

```env
# ─── Yandex Cloud ───
YANDEX_API_KEY=AQVN1XxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx
YANDEX_FOLDER_ID=b1gXXXXXXXXXXXXXXXXX

# ─── Источник ───
RSS_SOURCE_URL=https://lenta.ru/rss/news

# ─── Настройки ───
MAX_NEWS_ITEMS=10
OUTPUT_FILE=translated_news.xml
CACHE_FILE=.translation_cache.json
REQUEST_TIMEOUT=30
```

---

## 🎮 Использование

### Базовый запуск

```bash
python main.py
```

### CLI-аргументы

```bash
# Переопределить источник
python main.py --source https://habr.com/ru/rss/news

# Изменить лимит новостей
python main.py --limit 5

# Сохранить в другой файл
python main.py --output ./feeds/habr_en.xml

# Отключить кэш (полный перевод заново)
python main.py --no-cache

# Комбинация
python main.py --source https://tass.ru/rss/v2.xml --limit 20 --output tass_en.xml
```

---

## 📋 Пример вывода

```text
2024-01-15 14:32:10 [INFO] Загружено 47 записей из кэша
2024-01-15 14:32:10 [INFO] Парсинг RSS: https://lenta.ru/rss/news
2024-01-15 14:32:11 [INFO] Собрано 10 новостей
2024-01-15 14:32:11 [INFO] Перевод 8 текстов через API (в кэше 12)...
2024-01-15 14:32:13 [INFO] RSS сохранён: /home/user/project/translated_news.xml
2024-01-15 14:32:13 [INFO] Кэш сохранён: .translation_cache.json
```

### Результат — `translated_news.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">
  <channel>
    <title>Translated News</title>
    <link>https://cloud.yandex.com/</link>
    <description>News translated to English via Yandex Cloud API</description>
    <language>en</language>
    <item>
      <title>Russian Scientists Develop New Quantum Processor</title>
      <link>https://lenta.ru/news/2024/01/15/quantum/</link>
      <description>A team of physicists has presented...</description>
      <pubDate>Mon, 15 Jan 2024 10:00:00 +0000</pubDate>
    </item>
    <!-- ... -->
  </channel>
</rss>
```

---

## 🔧 Переменные окружения

| Переменная | Обязательная | По умолчанию | Описание |
|------------|:------------:|:------------:|----------|
| `YANDEX_API_KEY` | ✅ | — | API-ключ сервисного аккаунта Yandex |
| `YANDEX_FOLDER_ID` | ✅ | — | ID каталога в Yandex Cloud |
| `RSS_SOURCE_URL` | ❌ | `https://lenta.ru/rss/news` | URL RSS-источника |
| `MAX_NEWS_ITEMS` | ❌ | `10` | Количество новостей для обработки |
| `OUTPUT_FILE` | ❌ | `translated_news.xml` | Путь выходного XML |
| `CACHE_FILE` | ❌ | `.translation_cache.json` | Путь файла кэша |
| `REQUEST_TIMEOUT` | ❌ | `30` | Таймаут HTTP-запросов (сек) |

---

## 📈 Roadmap

- [x] Батчевый перевод
- [x] Файловый кэш (SHA256)
- [x] Retry с exponential backoff
- [x] CLI-аргументы
- [x] Graceful shutdown
- [ ] Асинхронная версия (`aiohttp`)
- [ ] Поддержка нескольких источников одновременно
- [ ] Docker-образ
- [ ] CI/CD (GitHub Actions)
- [ ] Поддержка YandexGPT API как альтернатива Translate
- [ ] Webhook-уведомления (Telegram, Slack)

---

## 🤝 Contributing

PR приветствуются! Пожалуйста:

1. Форкните репозиторий
2. Создайте ветку: `git checkout -b feature/amazing-feature`
3. Закоммитьте изменения: `git commit -m 'Add amazing feature'`
4. Запушьте: `git push origin feature/amazing-feature`
5. Откройте Pull Request

---

## 📄 Лицензия

Распространяется под лицензией **MIT**.  
См. файл [`LICENSE`](LICENSE) для подробностей.

---

<div align="center">

**Made with ❤️ and ☕**

</div>
