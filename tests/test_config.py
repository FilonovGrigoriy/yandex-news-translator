"""Tests for configuration module."""

import os
from pathlib import Path

import pytest

from main import Config, ConfigurationError


class TestConfig:
    """Test suite for Config dataclass."""

    def test_from_env_success(self, monkeypatch):
        """Config loads correctly when all required vars are set."""
        monkeypatch.setenv("YANDEX_API_KEY", "test_api_key")
        monkeypatch.setenv("YANDEX_FOLDER_ID", "test_folder_id")
        monkeypatch.setenv("RSS_SOURCE_URL", "https://example.com/rss")
        monkeypatch.setenv("MAX_NEWS_ITEMS", "5")
        monkeypatch.setenv("OUTPUT_FILE", "output.xml")
        monkeypatch.setenv("CACHE_FILE", "cache.json")

        config = Config.from_env()
        assert config.yandex_api_key == "test_api_key"
        assert config.yandex_folder_id == "test_folder_id"
        assert config.rss_source_url == "https://example.com/rss"
        assert config.max_news_items == 5
        assert config.output_file == Path("output.xml")
        assert config.cache_file == Path("cache.json")

    def test_from_env_missing_api_key(self, monkeypatch):
        """Raises ConfigurationError when YANDEX_API_KEY is missing."""
        monkeypatch.delenv("YANDEX_API_KEY", raising=False)
        monkeypatch.setenv("YANDEX_FOLDER_ID", "test_folder_id")

        with pytest.raises(ConfigurationError):
            Config.from_env()

    def test_from_env_missing_folder_id(self, monkeypatch):
        """Raises ConfigurationError when YANDEX_FOLDER_ID is missing."""
        monkeypatch.setenv("YANDEX_API_KEY", "test_api_key")
        monkeypatch.delenv("YANDEX_FOLDER_ID", raising=False)

        with pytest.raises(ConfigurationError):
            Config.from_env()

    def test_from_env_defaults(self, monkeypatch):
        """Uses default values for optional env variables."""
        monkeypatch.setenv("YANDEX_API_KEY", "test_api_key")
        monkeypatch.setenv("YANDEX_FOLDER_ID", "test_folder_id")
        monkeypatch.delenv("RSS_SOURCE_URL", raising=False)
        monkeypatch.delenv("MAX_NEWS_ITEMS", raising=False)
        monkeypatch.delenv("OUTPUT_FILE", raising=False)
        monkeypatch.delenv("CACHE_FILE", raising=False)

        config = Config.from_env()
        assert config.rss_source_url == "https://lenta.ru/rss/news"
        assert config.max_news_items == 10
        assert config.output_file == Path("translated_news.xml")
        assert config.cache_file == Path(".translation_cache.json")
