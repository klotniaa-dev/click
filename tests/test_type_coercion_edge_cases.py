"""Tests covering how parameter types coerce unusual input.

Covers edge cases for INT, FLOAT, Choice, Path, and IntRange types.
"""

import os

import pytest

import click


class TestIntegerCoercion:
    """An integer parameter given a non-numeric string."""

    def test_non_numeric_string_raises_bad_parameter(self):
        """INT rejects a non-numeric string with a descriptive message."""
        with pytest.raises(click.BadParameter) as exc_info:
            click.INT.convert("hello", None, None)

        assert "'hello' is not a valid integer" in exc_info.value.message

    def test_empty_string_raises_bad_parameter(self):
        """INT rejects an empty string."""
        with pytest.raises(click.BadParameter) as exc_info:
            click.INT.convert("", None, None)

        assert "is not a valid integer" in exc_info.value.message

    def test_float_string_raises_bad_parameter(self):
        """INT rejects a float-looking string like '3.14'."""
        with pytest.raises(click.BadParameter) as exc_info:
            click.INT.convert("3.14", None, None)

        assert "'3.14' is not a valid integer" in exc_info.value.message

    def test_whitespace_only_raises_bad_parameter(self):
        """INT rejects a whitespace-only string."""
        with pytest.raises(click.BadParameter) as exc_info:
            click.INT.convert("   ", None, None)

        assert "is not a valid integer" in exc_info.value.message

    def test_numeric_string_succeeds(self):
        """INT accepts a valid numeric string."""
        assert click.INT.convert("42", None, None) == 42

    def test_negative_numeric_string_succeeds(self):
        """INT accepts a negative numeric string."""
        assert click.INT.convert("-7", None, None) == -7


class TestFloatCoercion:
    """A float parameter given an integer-looking string."""

    def test_integer_looking_string_converts_to_float(self):
        """FLOAT converts '42' to 42.0 without error."""
        result = click.FLOAT.convert("42", None, None)
        assert result == 42.0
        assert isinstance(result, float)

    def test_negative_integer_looking_string_converts_to_float(self):
        """FLOAT converts '-7' to -7.0 without error."""
        result = click.FLOAT.convert("-7", None, None)
        assert result == -7.0
        assert isinstance(result, float)

    def test_zero_string_converts_to_float(self):
        """FLOAT converts '0' to 0.0."""
        result = click.FLOAT.convert("0", None, None)
        assert result == 0.0
        assert isinstance(result, float)

    def test_non_numeric_string_raises_bad_parameter(self):
        """FLOAT rejects a non-numeric string."""
        with pytest.raises(click.BadParameter) as exc_info:
            click.FLOAT.convert("abc", None, None)

        assert "'abc' is not a valid float" in exc_info.value.message

    def test_scientific_notation_succeeds(self):
        """FLOAT accepts scientific notation."""
        result = click.FLOAT.convert("1e3", None, None)
        assert result == 1000.0


class TestChoiceCaseSensitivity:
    """A choice parameter with case sensitivity toggled."""

    def test_case_sensitive_exact_match_succeeds(self):
        """Case-sensitive choice accepts exact match."""
        choice = click.Choice(["Foo", "Bar", "Baz"], case_sensitive=True)
        assert choice.convert("Foo", None, None) == "Foo"

    def test_case_sensitive_wrong_case_fails(self):
        """Case-sensitive choice rejects wrong case."""
        choice = click.Choice(["Foo", "Bar", "Baz"], case_sensitive=True)
        with pytest.raises(click.BadParameter) as exc_info:
            choice.convert("foo", None, None)

        assert "'foo' is not one of" in exc_info.value.message
        assert "Foo" in exc_info.value.message

    def test_case_insensitive_wrong_case_succeeds(self):
        """Case-insensitive choice accepts wrong case and returns original."""
        choice = click.Choice(["Foo", "Bar", "Baz"], case_sensitive=False)
        result = choice.convert("foo", None, None)
        # Returns the original choice value, not the input
        assert result == "Foo"

    def test_case_insensitive_upper_case_succeeds(self):
        """Case-insensitive choice accepts upper-cased input."""
        choice = click.Choice(["hello", "world"], case_sensitive=False)
        result = choice.convert("HELLO", None, None)
        assert result == "hello"

    def test_case_sensitive_invalid_choice_message_lists_choices(self):
        """Error message for invalid choice lists all valid choices."""
        choice = click.Choice(["alpha", "beta", "gamma"], case_sensitive=True)
        with pytest.raises(click.BadParameter) as exc_info:
            choice.convert("delta", None, None)

        message = exc_info.value.message
        assert "'delta' is not one of" in message
        assert "'alpha'" in message
        assert "'beta'" in message
        assert "'gamma'" in message

    def test_case_insensitive_invalid_choice_still_fails(self):
        """Case-insensitive choice still fails for completely invalid input."""
        choice = click.Choice(["yes", "no"], case_sensitive=False)
        with pytest.raises(click.BadParameter) as exc_info:
            choice.convert("maybe", None, None)

        assert "'maybe' is not one of" in exc_info.value.message


class TestPathExistence:
    """A path parameter for a file that does not exist, with existence both
    required and not."""

    def test_nonexistent_path_with_exists_required_fails(self, tmp_path):
        """Path with exists=True fails for a nonexistent file."""
        nonexistent = str(tmp_path / "does_not_exist.txt")
        path_type = click.Path(exists=True)

        with pytest.raises(click.BadParameter) as exc_info:
            path_type.convert(nonexistent, None, None)

        assert "does not exist" in exc_info.value.message
        assert "does_not_exist.txt" in exc_info.value.message

    def test_nonexistent_path_without_exists_required_succeeds(self, tmp_path):
        """Path with exists=False (default) succeeds for a nonexistent file."""
        nonexistent = str(tmp_path / "does_not_exist.txt")
        path_type = click.Path(exists=False)

        result = path_type.convert(nonexistent, None, None)
        assert result == nonexistent

    def test_existing_path_with_exists_required_succeeds(self, tmp_path):
        """Path with exists=True succeeds for an existing file."""
        existing = tmp_path / "exists.txt"
        existing.write_text("content")
        path_type = click.Path(exists=True)

        result = path_type.convert(str(existing), None, None)
        assert result == str(existing)

    def test_nonexistent_path_error_message_includes_path_type_name(self, tmp_path):
        """Error message uses 'Path' as the type name by default."""
        nonexistent = str(tmp_path / "gone.txt")
        path_type = click.Path(exists=True)

        with pytest.raises(click.BadParameter) as exc_info:
            path_type.convert(nonexistent, None, None)

        # The message format is: "Path 'filename' does not exist."
        assert "Path" in exc_info.value.message

    def test_nonexistent_file_only_path_error_uses_file_name(self, tmp_path):
        """When file_okay=True and dir_okay=False, the error says 'File'."""
        nonexistent = str(tmp_path / "missing.dat")
        path_type = click.Path(exists=True, file_okay=True, dir_okay=False)

        with pytest.raises(click.BadParameter) as exc_info:
            path_type.convert(nonexistent, None, None)

        assert "File" in exc_info.value.message
        assert "does not exist" in exc_info.value.message

    def test_nonexistent_dir_only_path_error_uses_directory_name(self, tmp_path):
        """When dir_okay=True and file_okay=False, the error says 'Directory'."""
        nonexistent = str(tmp_path / "missing_dir")
        path_type = click.Path(exists=True, file_okay=False, dir_okay=True)

        with pytest.raises(click.BadParameter) as exc_info:
            path_type.convert(nonexistent, None, None)

        assert "Directory" in exc_info.value.message
        assert "does not exist" in exc_info.value.message


class TestIntRangeBounds:
    """An integer range parameter at, below, and above its bounds."""

    def test_value_at_minimum_succeeds(self):
        """Value exactly at min is accepted."""
        range_type = click.IntRange(min=0, max=10)
        assert range_type.convert("0", None, None) == 0

    def test_value_at_maximum_succeeds(self):
        """Value exactly at max is accepted."""
        range_type = click.IntRange(min=0, max=10)
        assert range_type.convert("10", None, None) == 10

    def test_value_below_minimum_fails(self):
        """Value below min raises BadParameter with range description."""
        range_type = click.IntRange(min=0, max=10)
        with pytest.raises(click.BadParameter) as exc_info:
            range_type.convert("-1", None, None)

        assert "-1 is not in the range" in exc_info.value.message
        assert "0<=x<=10" in exc_info.value.message

    def test_value_above_maximum_fails(self):
        """Value above max raises BadParameter with range description."""
        range_type = click.IntRange(min=0, max=10)
        with pytest.raises(click.BadParameter) as exc_info:
            range_type.convert("11", None, None)

        assert "11 is not in the range" in exc_info.value.message
        assert "0<=x<=10" in exc_info.value.message

    def test_value_within_range_succeeds(self):
        """Value within the range is accepted."""
        range_type = click.IntRange(min=0, max=10)
        assert range_type.convert("5", None, None) == 5

    def test_open_min_at_boundary_fails(self):
        """With min_open=True, value exactly at min is rejected."""
        range_type = click.IntRange(min=0, max=10, min_open=True)
        with pytest.raises(click.BadParameter) as exc_info:
            range_type.convert("0", None, None)

        assert "0<x<=10" in exc_info.value.message

    def test_open_max_at_boundary_fails(self):
        """With max_open=True, value exactly at max is rejected."""
        range_type = click.IntRange(min=0, max=10, max_open=True)
        with pytest.raises(click.BadParameter) as exc_info:
            range_type.convert("10", None, None)

        assert "0<=x<10" in exc_info.value.message

    def test_min_only_below_fails(self):
        """Range with only min rejects values below it."""
        range_type = click.IntRange(min=5)
        with pytest.raises(click.BadParameter) as exc_info:
            range_type.convert("4", None, None)

        assert "4 is not in the range" in exc_info.value.message
        assert "x>=5" in exc_info.value.message

    def test_max_only_above_fails(self):
        """Range with only max rejects values above it."""
        range_type = click.IntRange(max=100)
        with pytest.raises(click.BadParameter) as exc_info:
            range_type.convert("101", None, None)

        assert "101 is not in the range" in exc_info.value.message
        assert "x<=100" in exc_info.value.message

    def test_clamp_below_minimum_returns_min(self):
        """With clamp=True, value below min is clamped to min."""
        range_type = click.IntRange(min=0, max=10, clamp=True)
        assert range_type.convert("-5", None, None) == 0

    def test_clamp_above_maximum_returns_max(self):
        """With clamp=True, value above max is clamped to max."""
        range_type = click.IntRange(min=0, max=10, clamp=True)
        assert range_type.convert("15", None, None) == 10
