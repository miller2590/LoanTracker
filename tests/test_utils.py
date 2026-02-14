"""Tests for currency utility functions."""

from __future__ import annotations

import pytest

from loantracker.utils.currency import format_currency, parse_currency


class TestFormatCurrency:
    """Tests for format_currency function."""

    def test_format_basic_value(self) -> None:
        """Test formatting a basic float value."""
        assert format_currency(100.50) == "100.50"

    def test_format_with_commas(self) -> None:
        """Test formatting large values with commas."""
        assert format_currency(1234.56) == "1,234.56"
        assert format_currency(1234567.89) == "1,234,567.89"

    def test_format_rounds_to_two_decimals(self) -> None:
        """Test that values are rounded to 2 decimal places."""
        assert format_currency(100.999) == "101.00"
        assert format_currency(100.994) == "100.99"

    def test_format_zero_returns_empty(self) -> None:
        """Test that zero returns empty string."""
        assert format_currency(0) == ""
        assert format_currency(0.0) == ""

    def test_format_none_returns_empty(self) -> None:
        """Test that None returns empty string."""
        assert format_currency(None) == ""

    def test_format_whole_number(self) -> None:
        """Test formatting whole numbers."""
        assert format_currency(100) == "100.00"
        assert format_currency(100000) == "100,000.00"


class TestParseCurrency:
    """Tests for parse_currency function."""

    def test_parse_basic_string(self) -> None:
        """Test parsing a basic numeric string."""
        assert parse_currency("100.50") == 100.50

    def test_parse_with_commas(self) -> None:
        """Test parsing strings with commas."""
        assert parse_currency("1,234.56") == 1234.56
        assert parse_currency("1,234,567.89") == 1234567.89

    def test_parse_with_dollar_sign(self) -> None:
        """Test parsing strings with dollar sign."""
        assert parse_currency("$100.50") == 100.50
        assert parse_currency("$1,234.56") == 1234.56

    def test_parse_integer_string(self) -> None:
        """Test parsing integer strings."""
        assert parse_currency("100") == 100.0
        assert parse_currency("100000") == 100000.0

    def test_parse_float_passthrough(self) -> None:
        """Test that float values pass through."""
        assert parse_currency(100.50) == 100.50

    def test_parse_int_passthrough(self) -> None:
        """Test that int values pass through."""
        assert parse_currency(100) == 100.0

    def test_parse_none_returns_zero(self) -> None:
        """Test that None returns 0.0."""
        assert parse_currency(None) == 0.0

    def test_parse_empty_string_returns_zero(self) -> None:
        """Test that empty string returns 0.0."""
        assert parse_currency("") == 0.0
        assert parse_currency("   ") == 0.0

    def test_parse_invalid_string_returns_zero(self) -> None:
        """Test that invalid strings return 0.0."""
        assert parse_currency("abc") == 0.0
        assert parse_currency("$abc") == 0.0

    def test_parse_with_whitespace(self) -> None:
        """Test parsing strings with whitespace."""
        assert parse_currency("  100.50  ") == 100.50
        assert parse_currency("  $1,234.56  ") == 1234.56

