"""Tests for parameter type coercion edge cases.

Covers unusual inputs for INT, FLOAT, Choice, Path, and IntRange types,
asserting on the actual failure behaviour and message shape.
"""

import os

import pytest

import click
from click import BadParameter


# ---------------------------------------------------------------------------
# INT parameter given a non-numeric string
# ---------------------------------------------------------------------------


class TestIntNonNumericString:
    """INT.convert should reject non-numeric strings with a clear message."""

    @pytest.mark.parametrize(
        "value",
        [
            "abc",
            "12.5",  # floats are not valid ints
            "",
            "NaN",
            "inf",
            "0x1A",  # hex literal strings are not accepted by int()
        ],
    )
    def test_int_rejects_non_numeric_string(self, value):
        with pytest.raises(BadParameter) as exc_info:
            click.INT.convert(value, None, None)

        # The error message should mention the value and "integer"
        assert repr(value) in exc_info.value.message or value in exc_info.value.message
        assert "integer" in exc_info.value.message

    def test_int_accepts_numeric_string(self):
        assert click.INT.convert("42", None, None) == 42

    def test_int_accepts_negative_string(self):
        assert click.INT.convert("-7", None, None) == -7

    def test_int_accepts_zero(self):
        assert click.INT.convert("0", None, None) == 0

    def test_int_message_format(self):
        """The error message should follow the pattern:
        '{value!r} is not a valid integer.'
        """
        with pytest.raises(BadParameter) as exc_info:
            click.INT.convert("notanumber", None, None)

        assert exc_info.value.message == "'notanumber' is not a valid integer."


# ---------------------------------------------------------------------------
# FLOAT parameter given an integer-looking string
# ---------------------------------------------------------------------------


class TestFloatIntegerLookingString:
    """FLOAT.convert should successfully coerce integer-looking strings."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("3", 3.0),
            ("-1", -1.0),
            ("0", 0.0),
            ("100", 100.0),
            ("007", 7.0),
        ],
    )
    def test_float_coerces_integer_string(self, value, expected):
        result = click.FLOAT.convert(value, None, None)
        assert result == expected
        assert isinstance(result, float)

    def test_float_accepts_scientific_notation(self):
        result = click.FLOAT.convert("1e3", None, None)
        assert result == 1000.0

    def test_float_accepts_inf(self):
        result = click.FLOAT.convert("inf", None, None)
        assert result == float("inf")

    def test_float_rejects_non_numeric(self):
        with pytest.raises(BadParameter) as exc_info:
            click.FLOAT.convert("notafloat", None, None)

        assert "float" in exc_info.value.message
        assert "'notafloat'" in exc_info.value.message

    def test_float_message_format(self):
        """Error message follows: '{value!r} is not a valid float.'"""
        with pytest.raises(BadParameter) as exc_info:
            click.FLOAT.convert("xyz", None, None)

        assert exc_info.value.message == "'xyz' is not a valid float."


# ---------------------------------------------------------------------------
# Choice parameter with case sensitivity toggled
# ---------------------------------------------------------------------------


class TestChoiceCaseSensitivity:
    """Choice type should respect the case_sensitive flag."""

    def test_case_sensitive_exact_match(self):
        choice = click.Choice(["Foo", "Bar", "Baz"], case_sensitive=True)
        assert choice.convert("Foo", None, None) == "Foo"

    def test_case_sensitive_rejects_wrong_case(self):
        choice = click.Choice(["Foo", "Bar", "Baz"], case_sensitive=True)
        with pytest.raises(BadParameter) as exc_info:
            choice.convert("foo", None, None)

        # Message should indicate the invalid value and available choices
        assert "'foo'" in exc_info.value.message
        assert "Foo" in exc_info.value.message

    def test_case_insensitive_accepts_any_case(self):
        choice = click.Choice(["Foo", "Bar", "Baz"], case_sensitive=False)
        # Should return the original choice value, not the user input
        assert choice.convert("foo", None, None) == "Foo"
        assert choice.convert("FOO", None, None) == "Foo"
        assert choice.convert("bAr", None, None) == "Bar"

    def test_case_insensitive_rejects_invalid_value(self):
        choice = click.Choice(["Foo", "Bar"], case_sensitive=False)
        with pytest.raises(BadParameter) as exc_info:
            choice.convert("Qux", None, None)

        assert "'Qux'" in exc_info.value.message

    def test_case_sensitive_message_lists_choices(self):
        """When case_sensitive=True, the error message shows choices as-is."""
        choice = click.Choice(["alpha", "beta"], case_sensitive=True)
        with pytest.raises(BadParameter) as exc_info:
            choice.convert("gamma", None, None)

        msg = exc_info.value.message
        assert "'gamma'" in msg
        assert "'alpha'" in msg
        assert "'beta'" in msg

    def test_case_insensitive_message_lists_casefolded_choices(self):
        """When case_sensitive=False, the error message shows casefolded choices."""
        choice = click.Choice(["Alpha", "Beta"], case_sensitive=False)
        with pytest.raises(BadParameter) as exc_info:
            choice.convert("gamma", None, None)

        msg = exc_info.value.message
        assert "'gamma'" in msg
        # Choices are casefolded in the message
        assert "'alpha'" in msg
        assert "'beta'" in msg

    def test_single_choice_error_uses_singular_form(self):
        """A single-item Choice uses 'is not' (singular) in the message."""
        choice = click.Choice(["only"], case_sensitive=True)
        with pytest.raises(BadParameter) as exc_info:
            choice.convert("other", None, None)

        # ngettext singular: "{value!r} is not {choice}."
        assert "is not" in exc_info.value.message

    def test_multiple_choices_error_uses_plural_form(self):
        """A multi-item Choice uses 'is not one of' (plural) in the message."""
        choice = click.Choice(["a", "b", "c"], case_sensitive=True)
        with pytest.raises(BadParameter) as exc_info:
            choice.convert("z", None, None)

        # ngettext plural: "{value!r} is not one of {choices}."
        assert "is not one of" in exc_info.value.message


# ---------------------------------------------------------------------------
# Path parameter for a file that does not exist
# ---------------------------------------------------------------------------


class TestPathExistence:
    """Path type should validate existence based on the exists flag."""

    def test_path_exists_required_missing_file(self, tmp_path):
        """When exists=True and file does not exist, it should fail."""
        missing = str(tmp_path / "nonexistent.txt")
        path_type = click.Path(exists=True)

        with pytest.raises(BadParameter) as exc_info:
            path_type.convert(missing, None, None)

        # Message mentions "does not exist" and the filename
        assert "does not exist" in exc_info.value.message
        assert "nonexistent.txt" in exc_info.value.message

    def test_path_exists_not_required_missing_file(self, tmp_path):
        """When exists=False (default), missing path is returned as-is."""
        missing = str(tmp_path / "nonexistent.txt")
        path_type = click.Path(exists=False)

        result = path_type.convert(missing, None, None)
        assert result == missing

    def test_path_exists_required_existing_file(self, tmp_path):
        """When exists=True and file exists, it should succeed."""
        existing = tmp_path / "exists.txt"
        existing.write_text("hello")
        path_type = click.Path(exists=True)

        result = path_type.convert(str(existing), None, None)
        assert result == str(existing)

    def test_path_exists_error_message_mentions_path_name(self, tmp_path):
        """The error message should include 'Path' as the name by default."""
        missing = str(tmp_path / "gone.txt")
        path_type = click.Path(exists=True)

        with pytest.raises(BadParameter) as exc_info:
            path_type.convert(missing, None, None)

        # Default name is "path" -> title-cased to "Path" in message
        assert "Path" in exc_info.value.message

    def test_path_file_okay_false_rejects_file(self, tmp_path):
        """When file_okay=False, an existing file should be rejected."""
        existing = tmp_path / "afile.txt"
        existing.write_text("data")
        path_type = click.Path(exists=True, file_okay=False)

        with pytest.raises(BadParameter) as exc_info:
            path_type.convert(str(existing), None, None)

        assert "is a file" in exc_info.value.message

    def test_path_dir_okay_false_rejects_directory(self, tmp_path):
        """When dir_okay=False, an existing directory should be rejected."""
        path_type = click.Path(exists=True, dir_okay=False)

        with pytest.raises(BadParameter) as exc_info:
            path_type.convert(str(tmp_path), None, None)

        assert "is a directory" in exc_info.value.message


# ---------------------------------------------------------------------------
# IntRange parameter at, below, and above its bounds
# ---------------------------------------------------------------------------


class TestIntRangeBounds:
    """IntRange should accept values at bounds and reject outside."""

    def test_at_lower_bound(self):
        range_type = click.IntRange(min=0, max=10)
        assert range_type.convert("0", None, None) == 0

    def test_at_upper_bound(self):
        range_type = click.IntRange(min=0, max=10)
        assert range_type.convert("10", None, None) == 10

    def test_below_lower_bound(self):
        range_type = click.IntRange(min=0, max=10)
        with pytest.raises(BadParameter) as exc_info:
            range_type.convert("-1", None, None)

        assert "-1 is not in the range" in exc_info.value.message
        assert "0<=x<=10" in exc_info.value.message

    def test_above_upper_bound(self):
        range_type = click.IntRange(min=0, max=10)
        with pytest.raises(BadParameter) as exc_info:
            range_type.convert("11", None, None)

        assert "11 is not in the range" in exc_info.value.message
        assert "0<=x<=10" in exc_info.value.message

    def test_open_lower_bound_rejects_boundary_value(self):
        """min_open=True means the minimum itself is excluded."""
        range_type = click.IntRange(min=0, max=10, min_open=True)
        with pytest.raises(BadParameter) as exc_info:
            range_type.convert("0", None, None)

        assert "0<x<=10" in exc_info.value.message

    def test_open_lower_bound_accepts_above_minimum(self):
        range_type = click.IntRange(min=0, max=10, min_open=True)
        assert range_type.convert("1", None, None) == 1

    def test_open_upper_bound_rejects_boundary_value(self):
        """max_open=True means the maximum itself is excluded."""
        range_type = click.IntRange(min=0, max=10, max_open=True)
        with pytest.raises(BadParameter) as exc_info:
            range_type.convert("10", None, None)

        assert "0<=x<10" in exc_info.value.message

    def test_open_upper_bound_accepts_below_maximum(self):
        range_type = click.IntRange(min=0, max=10, max_open=True)
        assert range_type.convert("9", None, None) == 9

    def test_clamping_below_minimum(self):
        """With clamp=True, values below min are clamped to min."""
        range_type = click.IntRange(min=5, max=15, clamp=True)
        assert range_type.convert("-100", None, None) == 5

    def test_clamping_above_maximum(self):
        """With clamp=True, values above max are clamped to max."""
        range_type = click.IntRange(min=5, max=15, clamp=True)
        assert range_type.convert("999", None, None) == 15

    def test_clamping_open_min_returns_min_plus_one(self):
        """With clamp=True and min_open=True, clamp to min+1."""
        range_type = click.IntRange(min=5, max=15, min_open=True, clamp=True)
        assert range_type.convert("5", None, None) == 6

    def test_clamping_open_max_returns_max_minus_one(self):
        """With clamp=True and max_open=True, clamp to max-1."""
        range_type = click.IntRange(min=5, max=15, max_open=True, clamp=True)
        assert range_type.convert("15", None, None) == 14

    def test_non_numeric_string_in_range(self):
        """Non-numeric input to IntRange should fail with integer error first."""
        range_type = click.IntRange(min=0, max=10)
        with pytest.raises(BadParameter) as exc_info:
            range_type.convert("abc", None, None)

        # IntRange inherits INT conversion, so the error mentions "integer"
        assert "integer" in exc_info.value.message

    def test_unbounded_min(self):
        """IntRange with only max set accepts any value below max."""
        range_type = click.IntRange(max=100)
        assert range_type.convert("-999999", None, None) == -999999

    def test_unbounded_max(self):
        """IntRange with only min set accepts any value above min."""
        range_type = click.IntRange(min=0)
        assert range_type.convert("999999", None, None) == 999999
