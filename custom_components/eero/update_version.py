"""The latest firmware version an eero's update entity reports.

Kept free of Home Assistant and package imports so it can be tested on its own.

The target firmware comes from the network's update manifest, which can lag
behind: an eero that has already installed the release (or that eero says has
nothing to install) would otherwise show a stale or phantom "update
available". eero's own per-device update_available flag is authoritative when
it says False. Idea from ColinSummers/home-assistant-eero (stale firmware fix).
"""

from __future__ import annotations


def latest_firmware_version(
    installed: str | None, target: str | None, update_available: bool | None
) -> str | None:
    """Return the version Home Assistant should treat as the latest."""
    if update_available is False:
        return installed or target
    return target or installed
