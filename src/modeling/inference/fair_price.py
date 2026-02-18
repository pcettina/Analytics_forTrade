"""Inference utilities for translating model probability into trade edge."""

from __future__ import annotations


def clamp_probability(value: float) -> float:
    if value <= 0.0:
        return 0.0001
    if value >= 1.0:
        return 0.9999
    return value


def implied_probability(price: float) -> float:
    if price <= 0.0 or price >= 1.0:
        raise ValueError("prediction market price must be in (0, 1)")
    return price


def edge_from_fair_probability(fair_prob: float, market_price: float) -> float:
    fair = clamp_probability(fair_prob)
    implied = implied_probability(market_price)
    return fair - implied
