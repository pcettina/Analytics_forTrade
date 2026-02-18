"""Core immutable domain models for the prediction-market stack."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True)
class MarketQuote:
    event_id: str
    market_id: str
    timestamp: datetime
    best_bid: float
    best_ask: float

    @property
    def mid_price(self) -> float:
        return (self.best_bid + self.best_ask) / 2.0


@dataclass(frozen=True)
class Signal:
    event_id: str
    market_id: str
    side: Side
    confidence: float
    expected_edge: float
    generated_at: datetime


@dataclass(frozen=True)
class OrderIntent:
    event_id: str
    market_id: str
    side: Side
    size: float
    limit_price: float
    created_at: datetime


@dataclass(frozen=True)
class RiskLimits:
    max_order_size: float
    max_market_exposure: float
    max_quote_age_seconds: int


@dataclass(frozen=True)
class Position:
    market_id: str
    size: float
    average_price: float


@dataclass(frozen=True)
class Fill:
    market_id: str
    side: Side
    size: float
    price: float
    timestamp: datetime


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
