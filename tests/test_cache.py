"""Tests for TranslationCache."""

import json
from pathlib import Path

from main import TranslationCache


class TestTranslationCache:
    """Test suite for TranslationCache."""

    def test_cache_miss(self, tmp_path):
        """Returns None for uncached text."""
        cache = TranslationCache(tmp_path / "cache.json")
        assert cache.get("hello world") is None

    def test_cache_set_and_get(self, tmp_path):
        """Stored translation can be retrieved."""
        cache = TranslationCache(tmp_path / "cache.json")
        cache.set("hello world", "привет мир")
        assert cache.get("hello world") == "привет мир"

    def test_cache_persistence(self, tmp_path):
        """Cache survives save/load cycle."""
        cache_file = tmp_path / "cache.json"
        cache = TranslationCache(cache_file)
        cache.set("foo", "bar")
        cache.save()

        new_cache = TranslationCache(cache_file)
        assert new_cache.get("foo") == "bar"

    def test_cache_different_texts(self, tmp_path):
        """Multiple texts are stored independently."""
        cache = TranslationCache(tmp_path / "cache.json")
        cache.set("a", "alpha")
        cache.set("b", "beta")
        assert cache.get("a") == "alpha"
        assert cache.get("b") == "beta"
        assert cache.get("c") is None

    def test_cache_load_corrupted(self, tmp_path, caplog):
        """Handles corrupted cache file gracefully."""
        cache_file = tmp_path / "cache.json"
        cache_file.write_text("not json", encoding="utf-8")
        cache = TranslationCache(cache_file)
        assert cache.get("anything") is None
