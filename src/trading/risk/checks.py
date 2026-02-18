"""Pre-trade risk checks with explicit rejection reasons."""

from __future__ import annotations

from datetime import datetime, timezone

from src.core.models import MarketQuote, OrderIntent, RiskLimits


def validate_order(order: OrderIntent, quote: MarketQuote, market_exposure: float, limits: RiskLimits) -> list[str]:
    reasons: list[str] = []

    if order.size <= 0:
        reasons.append("order size must be positive")
    if order.size > limits.max_order_size:
        reasons.append("order exceeds max_order_size")
    if abs(market_exposure + order.size) > limits.max_market_exposure:
        reasons.append("order exceeds max_market_exposure")

    now = datetime.now(timezone.utc)
    quote_age = (now - quote.timestamp).total_seconds()
    if quote_age > limits.max_quote_age_seconds:
        reasons.append("quote is stale")

    if not (quote.best_bid <= order.limit_price <= quote.best_ask):
        reasons.append("limit_price must be inside quoted spread")

    return reasons
