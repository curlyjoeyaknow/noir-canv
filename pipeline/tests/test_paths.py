"""Tests for pipeline path utilities and sandboxing."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.lib.paths import (
    DATA_DIR,
    OUTPUT_DIR,
    PUBLIC_DIR,
    _validate_slug,
    validate_output_path,
)


class TestValidateSlug:
    def test_accepts_simple_slug(self) -> None:
        _validate_slug("kai-voss")

    def test_accepts_slug_with_numbers(self) -> None:
        _validate_slug("artist42")

    def test_rejects_uppercase(self) -> None:
        with pytest.raises(ValueError, match="Invalid slug"):
            _validate_slug("Kai-Voss")

    def test_rejects_slug_starting_with_number(self) -> None:
        with pytest.raises(ValueError, match="Invalid slug"):
            _validate_slug("1bad-slug")

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ValueError, match="Invalid slug"):
            _validate_slug("")

    def test_rejects_path_traversal(self) -> None:
        with pytest.raises(ValueError, match="Invalid slug"):
            _validate_slug("../etc/passwd")

    def test_rejects_spaces(self) -> None:
        with pytest.raises(ValueError, match="Invalid slug"):
            _validate_slug("bad slug")

    def test_rejects_special_characters(self) -> None:
        with pytest.raises(ValueError, match="Invalid slug"):
            _validate_slug("slug!")


class TestValidateOutputPath:
    def test_accepts_path_in_output_dir(self) -> None:
        path = OUTPUT_DIR / "raw" / "artist" / "piece"
        result = validate_output_path(path)
        assert result == path.resolve()

    def test_accepts_path_in_data_dir(self) -> None:
        path = DATA_DIR / "artists.json"
        result = validate_output_path(path)
        assert result == path.resolve()

    def test_accepts_path_in_public_dir(self) -> None:
        path = PUBLIC_DIR / "images" / "pieces" / "test.png"
        result = validate_output_path(path)
        assert result == path.resolve()

    def test_rejects_path_outside_sandbox(self) -> None:
        path = Path("/tmp/malicious/file.json")
        with pytest.raises(ValueError, match="outside allowed"):
            validate_output_path(path)

    def test_rejects_parent_traversal(self) -> None:
        path = OUTPUT_DIR / ".." / ".." / "etc" / "passwd"
        with pytest.raises(ValueError, match="outside allowed"):
            validate_output_path(path)

    def test_rejects_home_directory(self) -> None:
        path = Path.home() / "Desktop" / "stolen.json"
        with pytest.raises(ValueError, match="outside allowed"):
            validate_output_path(path)
