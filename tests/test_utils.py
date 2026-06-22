"""Tests for utility functions."""

from datetime import datetime, timezone

import feedparser

from main import strip_html, parse_rss_date


class TestStripHtml:
    """Test suite for strip_html."""

    def test_removes_tags(self):
        assert strip_html("<p>Hello</p>") == "Hello"

    def test_unescapes_entities(self):
        assert strip_html("&lt;div&gt;") == "<div>"

    def test_normalizes_whitespace(self):
        assert strip_html("<p>  Hello   World  </p>") == "Hello World"

    def test_empty_string(self):
        assert strip_html("") == ""


class TestParseRssDate:
    """Test suite for parse_rss_date."""

    def test_published_parsed(self):
        entry = feedparser.FeedParserDict(
            published_parsed=(2024, 1, 15, 10, 30, 0, 0, 15, 0)
        )
        dt = parse_rss_date(entry)
        assert dt == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_updated_parsed_fallback(self):
        entry = feedparser.FeedParserDict(
            updated_parsed=(2024, 6, 22, 12, 0, 0, 0, 174, 0)
        )
        dt = parse_rss_date(entry)
        assert dt.year == 2024

    def test_no_date_fallback(self):
        entry = feedparser.FeedParserDict()
        dt = parse_rss_date(entry)
        assert isinstance(dt, datetime)
        assert dt.tzinfo == timezone.utc
