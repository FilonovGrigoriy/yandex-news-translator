#!/usr/bin/env python3
"""
News Parser and Translator — Improved Edition.

Улучшения:
- Батчевый перевод всех текстов одним запросом.
- Автоматический retry с exponential backoff.
- Локальный кэш переводов (JSON).
- Graceful shutdown.
- Очистка HTML-тегов.
- CLI-аргументы.
- Улучшенная обработка дат и валидация RSS.
"""

import argparse
import hashlib
import html
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import feedparser
import requests
from dotenv import load_dotenv
from feedgen.feed import FeedGenerator
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ───────────────────────────────────────────────────────────────
# Логирование
# ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────────
# Конфигурация
# ───────────────────────────────────────────────────────────────
load_dotenv()


class ConfigurationError(Exception):
    """Ошибка конфигурации."""


@dataclass(frozen=True)
class Config:
    """Конфигурация приложения."""

    yandex_api_key: str
    yandex_folder_id: str
    rss_source_url: str
    max_news_items: int
    output_file: Path
    cache_file: Path
    request_timeout: int = 30

    @classmethod
    def from_env(cls) -> "Config":
        """Загрузить конфигурацию из переменных окружения."""
        api_key = os.getenv("YANDEX_API_KEY")
        folder_id = os.getenv("YANDEX_FOLDER_ID")
        if not api_key or not folder_id:
            raise ConfigurationError(
                "YANDEX_API_KEY и YANDEX_FOLDER_ID должны быть заданы в .env"
            )

        return cls(
            yandex_api_key=api_key,
            yandex_folder_id=folder_id,
            rss_source_url=os.getenv("RSS_SOURCE_URL", "https://lenta.ru/rss/news"),
            max_news_items=int(os.getenv("MAX_NEWS_ITEMS", "10")),
            output_file=Path(os.getenv("OUTPUT_FILE", "translated_news.xml")),
            cache_file=Path(os.getenv("CACHE_FILE", ".translation_cache.json")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
        )


# ───────────────────────────────────────────────────────────────
# Модели
# ───────────────────────────────────────────────────────────────
@dataclass
class NewsItem:
    """Модель новости."""

    title: str
    link: str
    published: datetime
    summary: str

    def with_translated(self, title: str, summary: str) -> "NewsItem":
        """Вернуть копию с переведёнными полями."""
        return NewsItem(
            title=title,
            link=self.link,
            published=self.published,
            summary=summary,
        )


# ───────────────────────────────────────────────────────────────
# Утилиты
# ───────────────────────────────────────────────────────────────
def strip_html(raw: str) -> str:
    """Удалить HTML-теги и декодировать HTML-сущности."""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_rss_date(entry: feedparser.FeedParserDict) -> datetime:
    """Извлечь datetime из записи RSS с fallback'ами."""
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        if key in entry:
            try:
                return datetime(*entry[key][:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                continue

    for key in ("published", "updated", "created"):
        if key in entry:
            try:
                return parsedate_to_datetime(entry[key]).replace(tzinfo=timezone.utc)
            except Exception:
                continue

    return datetime.now(timezone.utc)


# ───────────────────────────────────────────────────────────────
# Кэш переводов
# ───────────────────────────────────────────────────────────────
class TranslationCache:
    """Простой файловый кэш переводов на основе SHA256 текста."""

    def __init__(self, cache_file: Path) -> None:
        self._cache_file = cache_file
        self._data: Dict[str, str] = {}
        self._load()

    def _make_key(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _load(self) -> None:
        if self._cache_file.exists():
            try:
                with self._cache_file.open("r", encoding="utf-8") as f:
                    self._data = json.load(f)
                logger.info("Загружено %d записей из кэша", len(self._data))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Не удалось загрузить кэш: %s", exc)
                self._data = {}

    def save(self) -> None:
        try:
            with self._cache_file.open("w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            logger.info("Кэш сохранён: %s", self._cache_file)
        except OSError as exc:
            logger.error("Не удалось сохранить кэш: %s", exc)

    def get(self, text: str) -> Optional[str]:
        return self._data.get(self._make_key(text))

    def set(self, text: str, translation: str) -> None:
        self._data[self._make_key(text)] = translation


# ───────────────────────────────────────────────────────────────
# Парсер RSS
# ───────────────────────────────────────────────────────────────
def fetch_news(feed_url: str, max_items: int) -> List[NewsItem]:
    """
    Собрать новости из RSS.

    Args:
        feed_url: URL RSS.
        max_items: Максимальное количество.

    Returns:
        Список NewsItem.

    Raises:
        RuntimeError: Если RSS недоступен или пуст.
    """
    logger.info("Парсинг RSS: %s", feed_url)
    feed = feedparser.parse(feed_url)

    if feed.bozo and isinstance(feed.bozo_exception, Exception):
        logger.warning("RSS-парсер сообщил о проблеме: %s", feed.bozo_exception)

    if not feed.entries:
        raise RuntimeError("RSS-лента пуста или недоступна")

    news_items: List[NewsItem] = []
    for entry in feed.entries[:max_items]:
        title = entry.get("title", "Untitled").strip()
        link = entry.get("link", "").strip()
        summary = strip_html(entry.get("summary", entry.get("description", "")))
        published = parse_rss_date(entry)

        if not link:
            continue

        news_items.append(
            NewsItem(title=title, link=link, published=published, summary=summary)
        )

    logger.info("Собрано %d новостей", len(news_items))
    return news_items


# ───────────────────────────────────────────────────────────────
# Переводчик (с retry и кэшем)
# ───────────────────────────────────────────────────────────────
class YandexTranslator:
    """Клиент Yandex Translate API с retry и кэшированием."""

    API_URL = "https://translate.api.cloud.yandex.net/translate/v2/translate"

    def __init__(self, config: Config, cache: TranslationCache) -> None:
        self._config = config
        self._cache = cache
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=4,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _translate_batch(self, texts: List[str]) -> List[str]:
        """
        Отправить батч текстов в API.

        Args:
            texts: Список строк.

        Returns:
            Список переведённых строк.
        """
        headers = {
            "Authorization": f"Api-Key {self._config.yandex_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "folderId": self._config.yandex_folder_id,
            "texts": texts,
            "targetLanguageCode": "en",
        }

        response = self._session.post(
            self.API_URL,
            json=payload,
            headers=headers,
            timeout=self._config.request_timeout,
        )
        response.raise_for_status()
        data = response.json()

        translations = data.get("translations", [])
        result = [t.get("text", "") for t in translations]

        if len(result) != len(texts):
            logger.warning(
                "Несоответствие: отправлено %d, получено %d",
                len(texts),
                len(result),
            )
            result.extend([""] * (len(texts) - len(result)))

        return result

    def translate_items(self, items: List[NewsItem]) -> List[NewsItem]:
        """
        Перевести список новостей с использованием кэша и батчевого API.

        Args:
            items: Список NewsItem.

        Returns:
            Список NewsItem с переведёнными полями.
        """
        if not items:
            return []

        # Собираем все тексты (title + summary для каждой новости)
        all_texts: List[str] = []
        for item in items:
            all_texts.extend([item.title, item.summary])

        # Проверяем кэш
        to_translate: List[str] = []
        index_map: List[int] = []
        results: List[Optional[str]] = [None] * len(all_texts)

        for i, text in enumerate(all_texts):
            cached = self._cache.get(text)
            if cached is not None:
                results[i] = cached
            else:
                to_translate.append(text)
                index_map.append(i)

        # Отправляем в API батчем
        if to_translate:
            logger.info(
                "Перевод %d текстов через API (в кэше %d)...",
                len(to_translate),
                len(all_texts) - len(to_translate),
            )
            try:
                api_results = self._translate_batch(to_translate)
            except requests.RequestException as exc:
                logger.error("Ошибка API: %s", exc)
                # Fallback: оставляем оригиналы
                for i in index_map:
                    results[i] = all_texts[i]
            else:
                for idx, global_idx in enumerate(index_map):
                    translated = api_results[idx]
                    original = all_texts[global_idx]
                    results[global_idx] = translated
                    self._cache.set(original, translated)
        else:
            logger.info("Все переводы найдены в кэше")

        # Собираем NewsItem обратно
        translated_items: List[NewsItem] = []
        for idx, item in enumerate(items):
            t = results[idx * 2] or item.title
            s = results[idx * 2 + 1] or item.summary
            translated_items.append(item.with_translated(t, s))

        return translated_items


# ───────────────────────────────────────────────────────────────
# Генерация RSS
# ───────────────────────────────────────────────────────────────
def generate_rss(
    items: List[NewsItem],
    output_path: Path,
    source_title: str = "Translated News",
) -> None:
    """
    Сформировать RSS-ленту.

    Args:
        items: Переведённые новости.
        output_path: Путь для сохранения.
        source_title: Заголовок ленты.
    """
    logger.info("Формирование RSS: %s", output_path)
    fg = FeedGenerator()
    fg.title(source_title)
    fg.description("News translated to English via Yandex Cloud API")
    fg.link(href="https://cloud.yandex.com/")
    fg.language("en")

    for item in items:
        entry = fg.add_entry()
        entry.title(item.title)
        entry.link(href=item.link)
        entry.description(item.summary)
        entry.published(item.published)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fg.rss_file(str(output_path))
    logger.info("RSS сохранён: %s", output_path.resolve())


# ───────────────────────────────────────────────────────────────
# CLI
# ───────────────────────────────────────────────────────────────
def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RSS News Parser and Translator")
    parser.add_argument("--source", dest="rss_source_url", help="URL RSS-источника")
    parser.add_argument(
        "--output", dest="output_file", type=Path, help="Путь для сохранения XML"
    )
    parser.add_argument(
        "--limit", dest="max_news_items", type=int, help="Максимум новостей"
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Не использовать кэш"
    )
    return parser


# ───────────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────────
def main() -> None:
    """Основная точка входа."""
    parser = build_arg_parser()
    cli_args = parser.parse_args()

    try:
        config = Config.from_env()
    except ConfigurationError as exc:
        logger.error("%s", exc)
        sys.exit(1)

    # CLI переопределяет env
    if cli_args.rss_source_url:
        config = Config(
            yandex_api_key=config.yandex_api_key,
            yandex_folder_id=config.yandex_folder_id,
            rss_source_url=cli_args.rss_source_url,
            max_news_items=cli_args.max_news_items or config.max_news_items,
            output_file=cli_args.output_file or config.output_file,
            cache_file=config.cache_file,
        )

    cache = TranslationCache(
        Path("/dev/null") if cli_args.no_cache else config.cache_file
    )
    translator = YandexTranslator(config, cache)

    try:
        news_items = fetch_news(config.rss_source_url, config.max_news_items)
        translated_items = translator.translate_items(news_items)

        if not translated_items:
            logger.error("Нет новостей для сохранения")
            sys.exit(1)

        generate_rss(translated_items, config.output_file)

    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
    except Exception as exc:
        logger.exception("Критическая ошибка: %s", exc)
        sys.exit(1)
    finally:
        if not cli_args.no_cache:
            cache.save()


if __name__ == "__main__":
    main()
