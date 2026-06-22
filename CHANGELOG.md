# Changelog

Все значимые изменения этого проекта будут документированы в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/),
и этот проект придерживается [Semantic Versioning](https://semver.org/lang/ru/).

## [1.0.0] — 2024-01-15

### Добавлено
- Парсинг RSS-источников через `feedparser`.
- Батчевый перевод текстов через Yandex Cloud Translate API.
- Файловый кэш переводов на основе SHA256.
- Автоматический retry с exponential backoff (urllib3).
- Генерация валидного RSS 2.0 через `feedgen`.
- CLI-аргументы (`--source`, `--limit`, `--output`, `--no-cache`).
- Graceful shutdown (обработка `Ctrl+C`).
- Очистка HTML-тегов и декодирование HTML-сущностей.
- Улучшенный fallback для парсинга дат публикаций.
- Полная документация (README, docstrings, type hints).
- GitHub Actions CI для линтинга и тестов.
- `pyproject.toml` для современной сборки.

[1.0.0]: https://github.com/FilonovGrigoriy/yandex-news-translator/releases/tag/v1.0.0
