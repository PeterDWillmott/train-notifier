"""Shared types and Protocols. Frozen once reviewed; stdlib only.

Time conventions:
- Every datetime is timezone-aware Europe/London (GMT in winter, BST in summer, handled by zoneinfo).
- Every bare `time` is local UK time truncated to the whole minute (Darwin working times with seconds are truncated).
- Midnight rollover is not supported.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum
from typing import Any, Literal, Protocol, Sequence
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")


def london_now() -> datetime:
    """Current time as tz-aware Europe/London."""
    return datetime.now(LONDON)


def _require_aware(value: datetime, label: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware (Europe/London)")


def _require_whole_minute(value: time, label: str) -> None:
    if value.tzinfo is not None:
        raise ValueError(f"{label} must be a naive local UK time")
    if value.second or value.microsecond:
        raise ValueError(f"{label} must be truncated to the whole minute")


@dataclass(frozen=True)
class StationRef:
    """A station. Darwin messages key on TIPLOC, so match on `tiploc`; `crs` is the public 3-letter code for display.

    One CRS can map to several TIPLOCs. Equality and hashing use `tiploc` only; `crs` is for display.
    Both codes are stripped and upper-cased on creation.
    """
    tiploc: str  # Darwin location code (the "tpl" field), e.g. "BTHNLGR"
    crs: str = field(compare=False)  # 3-letter CRS code, e.g. "RDG"; display only

    def __post_init__(self) -> None:
        object.__setattr__(self, "tiploc", self.tiploc.strip().upper())
        object.__setattr__(self, "crs", self.crs.strip().upper())
        if not (1 <= len(self.tiploc) <= 7 and self.tiploc.isascii() and self.tiploc.isalnum()):
            raise ValueError(f"tiploc must be 1-7 letters/digits, got {self.tiploc!r}")
        if not (len(self.crs) == 3 and self.crs.isascii() and self.crs.isalpha()):
            raise ValueError(f"crs must be 3 letters, got {self.crs!r}")


@dataclass(frozen=True)
class Leg:
    """One train service between two stations."""
    origin: StationRef
    destination: StationRef
    scheduled_departure: time  # local UK public time, whole minute; with origin + service date it is the matching key
    scheduled_arrival: time
    operator_toc: str | None = None
    headcode_hint: str | None = None

    def __post_init__(self) -> None:
        if self.origin == self.destination:
            raise ValueError("leg origin and destination must differ")
        _require_whole_minute(self.scheduled_departure, "scheduled_departure")
        _require_whole_minute(self.scheduled_arrival, "scheduled_arrival")
        if not self.scheduled_departure < self.scheduled_arrival:
            raise ValueError("leg must arrive after it departs (no midnight rollover)")


@dataclass(frozen=True)
class WatchedJourney:
    """A two-leg journey with a single interchange station.

    Multiple time slots and return trips are separate WatchedJourney objects.
    """
    id: str
    name: str  # e.g. "Morning 07:42"
    leg1: Leg  # origin -> interchange
    leg2: Leg  # interchange -> destination
    min_connection_mins: int = 5
    days_of_week: frozenset[int] = frozenset({0, 1, 2, 3, 4})  # Mon=0
    valid_from: date | None = None
    valid_to: date | None = None
    alert_window_mins_before: int = 90
    group: str | None = None  # optional label to group related time slots
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")
        days = frozenset(self.days_of_week)
        if not days or not days <= frozenset(range(7)):
            raise ValueError("days_of_week must be a non-empty subset of 0..6 (Mon=0)")
        object.__setattr__(self, "days_of_week", days)  # coerce so the journey stays hashable
        if self.min_connection_mins < 0:
            raise ValueError("min_connection_mins must be >= 0")
        if self.alert_window_mins_before <= 0:
            raise ValueError("alert_window_mins_before must be > 0")
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("valid_from must not be after valid_to")
        if self.leg1.destination != self.leg2.origin:
            raise ValueError("leg1.destination must equal leg2.origin")
        # Midnight rollover is not supported: all four times must be strictly in order within one day.
        if not (
            self.leg1.scheduled_departure
            < self.leg1.scheduled_arrival
            < self.leg2.scheduled_departure
            < self.leg2.scheduled_arrival
        ):
            raise ValueError("journey times must be strictly in order within one day (no midnight rollover)")
        dep = self.leg1.scheduled_departure
        if self.alert_window_mins_before > dep.hour * 60 + dep.minute:
            raise ValueError("alert window must not start before midnight (no midnight rollover)")

    @property
    def interchange(self) -> StationRef:
        """The single interchange station."""
        return self.leg1.destination


class StopStatus(str, Enum):
    """Status of a train at a stop (cancellations are a separate event, see TrainCancellation)."""
    on_time = "on_time"
    delayed = "delayed"
    unknown = "unknown"


@dataclass(frozen=True)
class TrainStopUpdate:
    """Normalised per-stop update derived from a Darwin train status (TS) message.

    scheduled_* are the public times (Darwin pta/ptd). Darwin "pass" entries (trains running
    through without stopping) are ignored and never become a TrainStopUpdate.
    All `time` fields are truncated to the whole minute.
    """
    train_id: str  # Darwin rid
    uid: str
    service_date: date
    headcode: str | None
    toc: str | None
    tiploc: str
    scheduled_departure: time | None
    scheduled_arrival: time | None
    estimated_departure: time | None  # Darwin "et" under dep
    estimated_arrival: time | None  # Darwin "et" under arr
    actual_departure: time | None  # Darwin "at" under dep
    actual_arrival: time | None  # Darwin "at" under arr
    platform: str | None
    status: StopStatus
    received_at: datetime  # tz-aware Europe/London

    def __post_init__(self) -> None:
        _require_aware(self.received_at, "received_at")
        for name in (
            "scheduled_departure", "scheduled_arrival", "estimated_departure",
            "estimated_arrival", "actual_departure", "actual_arrival",
        ):
            value = getattr(self, name)
            if value is not None:
                _require_whole_minute(value, name)


@dataclass(frozen=True)
class CancellationStop:
    """One location on a train's route, as listed in a Darwin schedule message."""
    tiploc: str
    scheduled_arrival: time | None  # public time (pta), whole minute
    scheduled_departure: time | None  # public time (ptd), whole minute
    cancelled: bool  # Darwin can="true" on this location

    def __post_init__(self) -> None:
        for name in ("scheduled_arrival", "scheduled_departure"):
            value = getattr(self, name)
            if value is not None:
                _require_whole_minute(value, name)


@dataclass(frozen=True)
class TrainCancellation:
    """Cancellation information derived from a Darwin schedule message.

    Cancellations arrive in schedule messages, not train status messages. A train is fully
    cancelled when every stop is cancelled, and part cancelled when only some are.
    """
    train_id: str  # Darwin rid
    uid: str
    service_date: date
    headcode: str | None  # Darwin trainId
    toc: str | None
    stops: tuple[CancellationStop, ...]
    cancel_reason: str | None  # Darwin numeric reason code, e.g. "920"; translated to text later
    received_at: datetime  # tz-aware Europe/London

    def __post_init__(self) -> None:
        _require_aware(self.received_at, "received_at")

    @property
    def fully_cancelled(self) -> bool:
        return bool(self.stops) and all(s.cancelled for s in self.stops)


NormalisedEvent = TrainStopUpdate | TrainCancellation  # what parse_message produces


class AlertKind(str, Enum):
    """Type of alert."""
    leg_delayed = "leg_delayed"
    leg_cancelled = "leg_cancelled"
    connection_at_risk = "connection_at_risk"
    connection_missed = "connection_missed"
    platform_change = "platform_change"
    recovered = "recovered"


@dataclass(frozen=True)
class Alert:
    """A notification to send for a watched journey."""
    journey_id: str
    kind: AlertKind
    severity: Literal["info", "warning", "urgent"]
    title: str
    body: str
    dedupe_key: str
    created_at: datetime  # tz-aware Europe/London
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_aware(self.created_at, "created_at")


class JourneyProvider(Protocol):
    """Source of watched journeys. `now` is tz-aware Europe/London."""
    def active_journeys(self, now: datetime) -> Sequence[WatchedJourney]: ...


class AlertStateStore(Protocol):
    """Dedupe and small key/value state for alerts."""
    def seen(self, dedupe_key: str) -> bool: ...
    def mark_sent(self, dedupe_key: str, at: datetime) -> None: ...
    def get_state(self, key: str) -> str | None: ...
    def set_state(self, key: str, value: str) -> None: ...


class Processor(Protocol):
    """Turns a decoded Darwin message into alerts."""
    def handle_raw(self, raw: dict) -> list[Alert]:
        """`raw` is the inner Darwin payload (the decoded JSON from the queue envelope's `bytes` field),
        e.g. {"ts": ..., "version": ..., "uR": {...}}. The queue envelope is unwrapped by the integration layer.
        Messages that carry no train data (e.g. a FailureResp heartbeat) must return [].
        """
        ...


class Notifier(Protocol):
    """Delivers an alert; raises NotifierError on failure."""
    def send(self, alert: Alert) -> None: ...


class NotifierError(Exception):
    """Raised when a notifier fails to deliver."""
