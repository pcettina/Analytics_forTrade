"""Signal generation from model fair value vs market quote."""

from __future__ import annotations

from src.core.models import MarketQuote, Side, Signal, utc_now
from src.modeling.inference.fair_price import edge_from_fair_probability


def build_signal(quote: MarketQuote, fair_probability: float, min_edge: float = 0.01) -> Signal | None:
    edge = edge_from_fair_probability(fair_probability, quote.mid_price)

    if abs(edge) < min_edge:
        return None

    side = Side.BUY if edge > 0 else Side.SELL
    confidence = min(1.0, abs(edge) * 10)
    return Signal(
        event_id=quote.event_id,
        market_id=quote.market_id,
        side=side,
        confidence=confidence,
        expected_edge=edge,
        generated_at=utc_now(),
    )
