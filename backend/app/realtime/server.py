"""Socket.IO server configuration (P2 ownership).

Mounted at /ws with namespace /investigations per Section 7 of docs/KYRO_TEAM_BIBLE.pdf.
"""

import socketio

# Initialize async Socket.IO server with ASGI mode
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
)

# ASGI Application wrapper for mounting into FastAPI
sio_app = socketio.ASGIApp(
    socketio_server=sio,
    socketio_path="socket.io",
)


@sio.on("connect", namespace="/investigations")
async def connect(sid: str, environ: dict, auth: dict = None):
    """Handle connection with token authentication placeholder."""
    # When P1 auth is available, token verification validates user & hospital_id
    token = auth.get("token") if auth else None
    return True


@sio.on("disconnect", namespace="/investigations")
async def disconnect(sid: str):
    """Handle client disconnection."""
    pass


@sio.on("join", namespace="/investigations")
async def handle_join(sid: str, data: dict):
    """Client joins room for a specific investigation: inv:{investigation_id}."""
    inv_id = data.get("investigation_id")
    if inv_id:
        room = f"inv:{inv_id}"
        await sio.enter_room(sid, room, namespace="/investigations")
        await sio.emit("joined", {"status": "joined", "room": room}, room=sid, namespace="/investigations")


@sio.on("leave", namespace="/investigations")
async def handle_leave(sid: str, data: dict):
    """Client leaves room."""
    inv_id = data.get("investigation_id")
    if inv_id:
        room = f"inv:{inv_id}"
        await sio.leave_room(sid, room, namespace="/investigations")
