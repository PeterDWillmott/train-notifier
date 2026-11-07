# This package is owned by the human; agents must not edit it.
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from contracts import Alert, AlertStateStore, JourneyProvider, london_now


class AlertEngine:
    """Stub engine: turns raw Darwin messages into alerts."""

    def __init__(self, journeys: JourneyProvider, state: AlertStateStore, clock: Callable[[], datetime] = london_now):
        self._journeys = journeys
        self._state = state
        self._clock = clock

    def handle_raw(self, raw: dict) -> list[Alert]:
        return []
