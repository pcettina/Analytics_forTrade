from datetime import datetime, timedelta, timezone

from src.analytics.pnl.compute import apply_fill, mark_to_market
from src.core.models import Fill, OrderIntent, Position, RiskLimits, Side
from src.ingestion.normalization.canonical import normalize_quote
from src.trading.risk.checks import validate_order
from src.trading.signal_engine.generator import build_signal


def test_quote_normalization_and_signal_creation():
    quote = normalize_quote(
        {
            "event_id": "evt-1",
            "market_id": "mkt-1",
            "ts": datetime.now(timezone.utc).isoformat(),
            "bid": 0.48,
            "ask": 0.52,
        }
    )

    signal = build_signal(quote, fair_probability=0.58, min_edge=0.02)
    assert signal is not None
    assert signal.side == Side.BUY


def test_risk_rejects_oversized_and_stale_order():
    old_ts = datetime.now(timezone.utc) - timedelta(seconds=90)
    quote = normalize_quote(
        {
            "event_id": "evt-1",
            "market_id": "mkt-1",
            "ts": old_ts.isoformat(),
            "bid": 0.40,
            "ask": 0.60,
        }
    )
    order = OrderIntent(
        event_id="evt-1",
        market_id="mkt-1",
        side=Side.BUY,
        size=120,
        limit_price=0.50,
        created_at=datetime.now(timezone.utc),
    )
    limits = RiskLimits(max_order_size=100, max_market_exposure=500, max_quote_age_seconds=30)
    reasons = validate_order(order, quote, market_exposure=0, limits=limits)
    assert "order exceeds max_order_size" in reasons
    assert "quote is stale" in reasons


def test_pnl_mark_to_market_long_position():
    position = Position(market_id="mkt-1", size=10, average_price=0.45)
    pnl = mark_to_market(position, mid_price=0.55)
    assert round(pnl, 6) == 1.0


def test_apply_fill_opens_new_position():
    fill = Fill(
        market_id="mkt-1",
        side=Side.BUY,
        size=5,
        price=0.50,
        timestamp=datetime.now(timezone.utc),
    )
    position = apply_fill(None, fill)
    assert position.size == 5
    assert position.average_price == 0.50
