"""Per-client Wi-Fi quality for the network's "Wi-Fi Clients" sensor.

Kept free of Home Assistant and package imports so it can be tested on its own.
Client entities only exist for clients selected in the options; this summary
covers every connected wireless client, so a dashboard can show signal, band
and the serving eero for all of them from one entity.
"""

from __future__ import annotations

import re
from typing import Any

_LEADING_NUMBER = re.compile(r"\s*(-?\d+(?:\.\d+)?)")


def _number(value: Any) -> float | None:
    """Leading number of '-57 dBm' / '52.0 MBit/s', or the value if numeric."""
    if isinstance(value, (int, float)):
        return value
    match = _LEADING_NUMBER.match(str(value or ""))
    return float(match.group(1)) if match else None


def band_for_frequency(frequency: Any) -> str | None:
    """'2.4', '5' or '6' (GHz) for a channel centre frequency in MHz."""
    mhz = _number(frequency)
    if mhz is None:
        return None
    if mhz >= 5925:
        return "6"
    if mhz >= 4900:
        return "5"
    return "2.4"


def summarize_wireless_clients(clients: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Connected wireless clients, weakest signal first (unknown signal last)."""
    rows = []
    for client in clients:
        if not client or not client.get("connected") or not client.get("wireless"):
            continue
        connectivity = client.get("connectivity") or {}
        source = client.get("source") or {}
        signal = _number(connectivity.get("signal"))
        rows.append(
            {
                "name": client.get("nickname")
                or client.get("display_name")
                or client.get("hostname")
                or client.get("mac"),
                "mac": client.get("mac"),
                "ip": client.get("ip"),
                "eero": source.get("location"),
                "band": band_for_frequency(connectivity.get("frequency")),
                "channel": client.get("channel"),
                "signal": int(signal) if signal is not None else None,
                "snr": connectivity.get("snr"),
                "bars": connectivity.get("score_bars"),
                "rx_rate": _number(connectivity.get("rx_bitrate")),
            }
        )
    rows.sort(key=lambda row: (row["signal"] is None, row["signal"] or 0))
    return rows
