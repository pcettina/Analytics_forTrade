"""Canonicalization helpers for ingesting external quote payloads."""

from __future__ import annotations

from datetime import datetime

from src.core.models import MarketQuote


def normalize_quote(payload: dict) -> MarketQuote:
    """Normalize heterogeneous feed payload into a canonical quote.

    Expected keys:
      - event_id
      - market_id
      - ts (ISO-8601)
      - bid
      - ask
    """
    bid = float(payload["bid"])
    ask = float(payload["ask"])
    if ask <= bid:
        raise ValueError("ask must be greater than bid")

    ts = datetime.fromisoformat(payload["ts"])
    return MarketQuote(
        event_id=str(payload["event_id"]),
        market_id=str(payload["market_id"]),
        timestamp=ts,
        best_bid=bid,
        best_ask=ask,
    )
