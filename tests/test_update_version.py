"""Tests for the latest firmware version an update entity reports."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "update_version",
    Path(__file__).parent.parent / "custom_components/eero/update_version.py",
)
update_version = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(update_version)
latest = update_version.latest_firmware_version


def test_update_available_reports_the_target() -> None:
    assert latest("v7.17.1", "v7.17.2", True) == "v7.17.2"


def test_no_update_available_reports_the_installed_version() -> None:
    """A stale manifest must not produce a phantom update."""
    assert latest("v7.17.2", "v7.18.0", False) == "v7.17.2"


def test_unknown_flag_trusts_the_target() -> None:
    assert latest("v7.17.1", "v7.17.2", None) == "v7.17.2"


def test_missing_values_fall_back_to_whatever_is_known() -> None:
    assert latest(None, "v7.17.2", False) == "v7.17.2"
    assert latest("v7.17.2", None, True) == "v7.17.2"
    assert latest(None, None, None) is None
