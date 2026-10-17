"""Real-time Socket.IO communication package for Kyro (P2 ownership)."""

from backend.app.realtime.emit import emit_event
from backend.app.realtime.server import sio, sio_app

__all__ = ["sio", "sio_app", "emit_event"]
