"""How each eero reaches the network: wired or wireless, and through what."""

from __future__ import annotations

import re
from typing import Any

BACKHAUL_WIRED = "wired"
BACKHAUL_WIRELESS = "wireless"

_SPEED = re.compile(r"^P(\d+)$")
_SERIAL = re.compile(r"\b([A-Z0-9]{12,})$")


def backhaul_type(eero: dict[str, Any]) -> str | None:
    """Return wired or wireless, or None when eero doesn't say."""
    wired = eero.get("wired")
    if wired is None:
        return None
    return BACKHAUL_WIRED if wired else BACKHAUL_WIRELESS


def _ports(eero: dict[str, Any]) -> list[dict[str, Any]]:
    return [p for p in ((eero.get("ethernet_status") or {}).get("statuses") or []) if p]


def link_speed_mbps(eero: dict[str, Any]) -> int | None:
    """Speed of the fastest connected Ethernet port ("P2500" -> 2500)."""
    speeds = [
        int(m.group(1))
        for p in _ports(eero)
        if p.get("hasCarrier") and (m := _SPEED.match(str(p.get("speed") or "")))
    ]
    return max(speeds, default=None)


def wired_neighbor_serials(eero: dict[str, Any]) -> list[str]:
    """Serials of other eeros seen over LLDP on this eero's connected ports.

    eero reports LLDP neighbors as "eero Pro 6E <serial>". Eeros that see each
    other this way share a wired segment (for example the same switch).
    """
    serials = set()
    for port in _ports(eero):
        if not port.get("hasCarrier"):
            continue
        for neighbor in port.get("lldpInfo") or []:
            if (neighbor or {}).get("systemName") != "eero":
                continue
            if m := _SERIAL.search(str(neighbor.get("systemDescription") or "")):
                serials.add(m.group(1))
    return sorted(serials)


def summarize_backhaul(
    eero: dict[str, Any], locations_by_serial: dict[str, str]
) -> dict[str, Any]:
    """Attributes describing this eero's uplink, for the Backhaul sensor."""
    upstream = eero.get("wireless_upstream_node") or {}
    radio = upstream.get("primary_mesh_radio")
    return {
        "upstream_eero": upstream.get("name"),
        "upstream_band": radio.removesuffix("GHz").strip() if radio else None,
        "link_speed_mbps": link_speed_mbps(eero),
        "wired_neighbors": sorted(
            locations_by_serial.get(serial, serial)
            for serial in wired_neighbor_serials(eero)
        ),
        "primary_node": eero.get("is_primary_node"),
    }
