"""Tests for how each eero reaches the network (wired or wireless backhaul)."""

from __future__ import annotations

from types import SimpleNamespace

from helpers import eero_api

backhaul = eero_api.backhaul


def port(carrier, speed, *neighbors):
    return {
        "interfaceNumber": 1, "hasCarrier": carrier, "speed": speed, "isWanPort": carrier,
        "lldpInfo": [
            {"systemName": "eero", "systemDescription": f"eero Pro 6E {serial}",
             "portId": "1", "portDescription": "eth1"}
            for serial in neighbors
        ],
    }


def eero(location, serial, *, wired, ports=(), upstream=None, primary=False, bars=5):
    return {
        "location": location, "serial": serial, "wired": wired, "is_primary_node": primary,
        "mesh_quality_bars": bars, "ethernet_status": {"statuses": list(ports)},
        "wireless_upstream_node": upstream, "url": f"/2.2/eeros/{serial}",
    }


OFFICE = eero("Office", "GGB1AAAA0000001", wired=True, primary=True,
              ports=[port(True, "P2500", "GGB1AAAA0000002"), port(False, "P10")])
DINING = eero("Dining Room", "GGB1AAAA0000002", wired=True,
              ports=[port(True, "P1000", "GGB1AAAA0000001")])
LIVING = eero("Living Room", "GGB1AAAA0000003", wired=False, ports=[port(False, "P10")],
              upstream={"name": "Dining Room", "primary_mesh_radio": "6GHz",
                        "node_or_proxied_node_id": 2, "is_proxied_node": False})


def test_type() -> None:
    assert backhaul.backhaul_type(OFFICE) == "wired"
    assert backhaul.backhaul_type(LIVING) == "wireless"
    assert backhaul.backhaul_type({}) is None


def test_link_speed_uses_connected_ports_only() -> None:
    assert backhaul.link_speed_mbps(OFFICE) == 2500
    assert backhaul.link_speed_mbps(DINING) == 1000
    assert backhaul.link_speed_mbps(LIVING) is None
    assert backhaul.link_speed_mbps({"ethernet_status": {"statuses": [port(True, "odd")]}}) is None


def test_summary_resolves_neighbor_serials_to_locations() -> None:
    names = {"GGB1AAAA0000001": "Office", "GGB1AAAA0000002": "Dining Room"}
    assert backhaul.summarize_backhaul(OFFICE, names) == {
        "upstream_eero": None, "upstream_band": None, "link_speed_mbps": 2500,
        "wired_neighbors": ["Dining Room"], "primary_node": True,
    }
    assert backhaul.summarize_backhaul(LIVING, names) == {
        "upstream_eero": "Dining Room", "upstream_band": "6", "link_speed_mbps": None,
        "wired_neighbors": [], "primary_node": False,
    }
    # An eero we don't know (another network, or not yet reported) keeps its serial.
    assert backhaul.summarize_backhaul(DINING, {})["wired_neighbors"] == ["GGB1AAAA0000001"]


def test_missing_or_null_blocks_do_not_raise() -> None:
    odd = {"wired": True, "ethernet_status": None, "wireless_upstream_node": None,
           "is_primary_node": None}
    assert backhaul.summarize_backhaul(odd, {})["wired_neighbors"] == []
    odd = {"ethernet_status": {"statuses": [None, {"hasCarrier": True, "lldpInfo": [None]}]}}
    assert backhaul.wired_neighbor_serials(odd) == []
    assert backhaul.link_speed_mbps(odd) is None


def test_device_properties() -> None:
    network = SimpleNamespace()
    devices = [eero_api.eero.EeroDevice(None, network, data) for data in (OFFICE, DINING, LIVING)]
    network.eeros = devices
    office, dining, living = devices
    assert office.backhaul == "wired" and living.backhaul == "wireless"
    assert office.mesh_quality_bars == 5
    assert dining.backhaul_details["wired_neighbors"] == ["Office"]
    assert living.backhaul_details["upstream_eero"] == "Dining Room"
