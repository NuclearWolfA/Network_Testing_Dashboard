import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from dateutil import parser as dateutil_parser


@dataclass
class ParseResult:
    status: str
    payload_text: str | None
    packet: dict[str, Any] | None
    fingerprint: str | None


def _pick(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=UTC)
    if isinstance(value, str):
        if value.isdigit():
            return datetime.fromtimestamp(int(value), tz=UTC)
        try:
            parsed = dateutil_parser.parse(value)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed
        except (ValueError, TypeError):
            return None
    return None


def _extract_inner(body: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(body, dict):
        return None
    candidates: list[Any] = [
        body,
        body.get("packet"),
        body.get("payload"),
        body.get("decoded"),
        body.get("data"),
    ]
    for candidate in candidates:
        if isinstance(candidate, dict) and any(
            key in candidate
            for key in ["from", "from_node", "sender", "id", "type", "payload", "to", "timestamp"]
        ):
            return candidate
    return None


def parse_meshtastic_payload(topic: str, payload_raw: bytes) -> ParseResult:
    text: str | None = None
    try:
        text = payload_raw.decode("utf-8")
    except UnicodeDecodeError:
        return ParseResult(status="raw_binary", payload_text=None, packet=None, fingerprint=None)

    encoded_topic = "/e/" in topic

    try:
        envelope = json.loads(text)
    except json.JSONDecodeError:
        if encoded_topic:
            return ParseResult(status="encoded_topic_unparsed", payload_text=text, packet=None, fingerprint=None)
        return ParseResult(status="unparsable_json", payload_text=text, packet=None, fingerprint=None)

    inner = _extract_inner(envelope)
    if inner is None:
        if encoded_topic:
            return ParseResult(status="encoded_topic_unparsed", payload_text=text, packet=None, fingerprint=None)
        return ParseResult(status="no_inner_packet", payload_text=text, packet=None, fingerprint=None)

    packet = {
        "channel": _pick(inner, "channel", "chan"),
        "from_node": _to_int(_pick(inner, "from", "from_node", "fromId")),
        "hop_start": _to_int(_pick(inner, "hop_start", "hopStart")),
        "hops_away": _to_int(_pick(inner, "hops_away", "hopsAway")),
        "inner_packet_id": str(_pick(inner, "id", "packet_id")) if _pick(inner, "id", "packet_id") is not None else None,
        "sender": _to_int(_pick(inner, "sender", "sender_id")),
        "packet_timestamp": _to_datetime(_pick(inner, "timestamp", "time", "ts")),
        "to_node": _to_int(_pick(inner, "to", "to_node", "toId")),
        "packet_type": _pick(inner, "type", "portnum", "packet_type"),
        "payload": _pick(inner, "payload", "decoded", "data"),
        "next_hop": _to_int(_pick(inner, "next_hop", "nextHop")),
        "relay_node": _to_int(_pick(inner, "relay_node", "relayNode", "via")),
        "rssi": _to_float(_pick(inner, "rssi")),
        "snr": _to_float(_pick(inner, "snr")),
        "route": _pick(inner, "route", "path"),
    }

    fingerprint_source = {
        "channel": packet["channel"],
        "from_node": packet["from_node"],
        "inner_packet_id": packet["inner_packet_id"],
        "sender": packet["sender"],
        "packet_timestamp": packet["packet_timestamp"].isoformat() if packet["packet_timestamp"] else None,
        "to_node": packet["to_node"],
        "packet_type": packet["packet_type"],
        "payload": packet["payload"],
    }
    fingerprint = hashlib.sha256(json.dumps(fingerprint_source, sort_keys=True, default=str).encode("utf-8")).hexdigest()

    return ParseResult(status="parsed", payload_text=text, packet=packet, fingerprint=fingerprint)
