"""
Per-chat memory so follow-up questions work ("what about 3 classes a semester?", "compare them").

Keyed by the session_id the UI sends. Kept in memory: it resets when the server restarts and
isn't shared between multiple containers, which is fine for a single-server demo.
Switching to a different student in the same session starts fresh.
"""

import threading
import time

MAX_AGE_SECONDS = 4 * 60 * 60

_sessions: dict[str, dict] = {}
_lock = threading.Lock()


def get(session_id: str | None, student_id: str | None) -> dict:
    if not session_id:
        return {}
    with _lock:
        state = _sessions.get(session_id)
        if not state or time.time() - state["_touched"] > MAX_AGE_SECONDS:
            return {}
        if state.get("student_id") != student_id:
            return {}
        return {k: (list(v) if isinstance(v, list) else v) for k, v in state.items()}


def update(session_id: str | None, student_id: str | None, **values) -> None:
    if not session_id:
        return
    with _lock:
        state = _sessions.get(session_id)
        if not state or state.get("student_id") != student_id:
            state = {"student_id": student_id, "plan_names": []}
            _sessions[session_id] = state
        state.update(values)
        state["_touched"] = time.time()
