"""Event emitter utility for real-time investigation updates (P2 ownership).

Emits monotonic seq events to room inv:{investigation_id} per Section 7 of docs/KYRO_TEAM_BIBLE.pdf.
"""

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from backend.app.realtime.server import sio

# Monotonic sequence counter per investigation (in-memory fallback; Redis INCR in production)
_seq_counters: Dict[str, int] = {}


def get_next_seq(investigation_id: UUID) -> int:
    """Retrieve next monotonic sequence number for an investigation."""
    key = str(investigation_id)
    _seq_counters[key] = _seq_counters.get(key, 0) + 1
    return _seq_counters[key]


async def emit_event(
    investigation_id: UUID,
    event: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Emit an investigation event formatted per Section 5 & 7 contract."""
    seq = get_next_seq(investigation_id)
    payload = {
        "event": event,
        "investigation_id": str(investigation_id),
        "seq": seq,
        "ts": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }

    room = f"inv:{investigation_id}"
    await sio.emit(
        event,
        payload,
        room=room,
        namespace="/investigations",
    )
    return payload
