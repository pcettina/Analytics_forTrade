# Implementation Plan (Phase 1)

This plan operationalizes `IMPLEMENTATION_PARADIGM.md` into concrete build steps for an initial executable skeleton.

## Goal
Deliver a minimal, testable vertical slice from quote ingestion to signal generation with risk gating and PnL estimation.

## Phase 1 Scope
- Canonical domain entities in `src/core/models.py`.
- Quote normalization in `src/ingestion/normalization/canonical.py`.
- Fair probability and edge computation in `src/modeling/inference/fair_price.py`.
- Signal generation in `src/trading/signal_engine/generator.py`.
- Pre-trade risk checks in `src/trading/risk/checks.py`.
- Realized/unrealized PnL primitives in `src/analytics/pnl/compute.py`.
- Unit tests in `tests/unit/`.

## Out of Scope (Phase 1)
- External exchange integrations.
- Real-time websocket ingestion.
- Front-end dashboards.
- Live order routing.

## Implementation Pattern
1. Keep all core entities immutable dataclasses.
2. Keep math functions pure and deterministic.
3. Keep risk checks explicit (accept/reject with reasons).
4. Keep tests focused on business invariants.

## Success Criteria
- End-to-end construction of signal from canonical quote + model fair probability.
- Risk engine rejects oversize orders and stale markets.
- PnL functions produce deterministic outputs for simple scenarios.
