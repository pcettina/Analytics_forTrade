"""Simple PnL primitives for paper-trading analytics."""

from __future__ import annotations

from src.core.models import Fill, Position, Side


def apply_fill(position: Position | None, fill: Fill) -> Position:
    signed_size = fill.size if fill.side == Side.BUY else -fill.size

    if position is None:
        return Position(market_id=fill.market_id, size=signed_size, average_price=fill.price)

    new_size = position.size + signed_size
    if new_size == 0:
        return Position(market_id=fill.market_id, size=0.0, average_price=0.0)

    same_direction = (position.size >= 0 and signed_size >= 0) or (position.size <= 0 and signed_size <= 0)
    if same_direction:
        weighted_notional = abs(position.size) * position.average_price + abs(signed_size) * fill.price
        avg = weighted_notional / abs(new_size)
        return Position(market_id=fill.market_id, size=new_size, average_price=avg)

    return Position(market_id=fill.market_id, size=new_size, average_price=position.average_price)


def mark_to_market(position: Position, mid_price: float) -> float:
    if position.size == 0:
        return 0.0
    return (mid_price - position.average_price) * position.size
