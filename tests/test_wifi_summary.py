"""Tests for the network's Wi-Fi client summary."""

from __future__ import annotations

from helpers import eero_api

wifi = eero_api.wifi_summary


def client(name, signal, frequency, connected=True, wireless=True, **extra):
    return {
        "nickname": name, "mac": f"aa:bb:cc:00:00:{len(name):02x}", "ip": "192.168.24.9",
        "connected": connected, "wireless": wireless, "channel": 36,
        "source": {"location": "Office"},
        "connectivity": {"signal": signal, "frequency": frequency, "snr": 30,
                         "score_bars": 4, "rx_bitrate": "52.0 MBit/s"},
        **extra,
    }


def test_weakest_first_and_only_connected_wireless() -> None:
    rows = wifi.summarize_wireless_clients([
        client("strong", "-40 dBm", 5180),
        client("weak", "-79 dBm", 2412),
        client("offline", "-50 dBm", 5180, connected=False),
        client("wired", None, None, wireless=False),
        client("unknown", None, 5955),
    ])
    assert [r["name"] for r in rows] == ["weak", "strong", "unknown"]
    weak = rows[0]
    assert weak["signal"] == -79 and weak["band"] == "2.4" and weak["eero"] == "Office"
    assert weak["rx_rate"] == 52.0 and weak["bars"] == 4
    assert rows[2]["signal"] is None and rows[2]["band"] == "6"


def test_name_falls_back_to_display_name_hostname_then_mac() -> None:
    rows = wifi.summarize_wireless_clients([
        {**client("", "-50 dBm", 5180), "nickname": None, "display_name": None,
         "hostname": "lwip0"},
    ])
    assert rows[0]["name"] == "lwip0"


def test_band_boundaries() -> None:
    assert wifi.band_for_frequency(2462) == "2.4"
    assert wifi.band_for_frequency(5745) == "5"
    assert wifi.band_for_frequency(5955) == "6"
    assert wifi.band_for_frequency(None) is None


def test_missing_or_null_blocks_do_not_raise() -> None:
    rows = wifi.summarize_wireless_clients([
        None,
        {"connected": True, "wireless": True, "mac": "aa", "connectivity": None, "source": None},
    ])
    assert rows == [{"name": "aa", "mac": "aa", "ip": None, "eero": None, "band": None,
                     "channel": None, "signal": None, "snr": None, "bars": None, "rx_rate": None}]
