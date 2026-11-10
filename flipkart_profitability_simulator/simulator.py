"""Deterministic, illustrative Flipkart classroom economics. Not historical estimates."""
from dataclasses import dataclass, asdict
from typing import Dict
import math

BASE_COSTS = {
    "Vendors": 65.0,
    "Discounts": 30.0,
    "Marketing & promotions": 12.0,
    "Technology": 8.0,
    "Logistics": 7.0,
    "Warehousing": 5.0,
    "Packaging": 3.0,
    "Payment gateways": 2.0,
    "Others": 3.0,
}
# Fraction that changes with volume; other fraction is committed for the period.
VARIABLE_SHARES = {
    "Vendors": 1.0, "Discounts": 1.0,
    "Marketing & promotions": 0.45, "Technology": 0.20,
    "Logistics": 0.90, "Warehousing": 0.45,
    "Packaging": 1.0, "Payment gateways": 1.0, "Others": 0.35,
}
DESCRIPTIONS = {
    "Vendors": "Cheaper procurement / narrower selection; can reduce product availability.",
    "Discounts": "Lower promotional subsidies; can weaken conversion and demand.",
    "Marketing & promotions": "Less customer acquisition spend; can reduce new-customer demand.",
    "Technology": "Lower platform expenditure; can affect reliability and conversion.",
    "Logistics": "Lower delivery spend; can delay or disrupt delivery.",
    "Warehousing": "Lower fulfilment capacity; can increase stock-outs and lead times.",
    "Packaging": "Lower protection costs; may increase returns and damage.",
    "Payment gateways": "Lower payment-processing spend; may increase checkout failures.",
    "Others": "Lower customer-support and overhead spend; may affect service experience.",
}
DEFAULT_RULES = {
    "min_revenue_p1": 90.0,
    "max_loss_p1": 20.0,
    "min_satisfaction": 70.0,
    "min_revenue_p2": 90.0,
    "opening_cash": 35.0,
}


def clamp(x, low, high):
    return max(low, min(high, x))


def evaluate(cuts: Dict[str, float], rules=None):
    """cuts are 0..50 percent reduction in each named expense per baseline order.

    Simplified retail-like P&L: reference revenue = 100, cost = 135. Discounts
    are modeled *once* as an explicit outlay, to reproduce the original exhibit.
    No real Flipkart elasticity, valuation, or accounting is being asserted.
    """
    rules = {**DEFAULT_RULES, **(rules or {})}
    if set(cuts) != set(BASE_COSTS):
        raise ValueError("Provide exactly the nine named cost heads")
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 or v > 50 for v in cuts.values()):
        raise ValueError("Cost reductions must be finite values between 0 and 50 percent")

    r = {k: cuts[k] / 100 for k in BASE_COSTS}
    # Cost cuts lower service quality and the firm's attractiveness.
    service_penalty = (18*r["Logistics"] + 13*r["Warehousing"] +
                       15*r["Technology"] + 10*r["Packaging"] +
                       10*r["Payment gateways"] + 10*r["Others"] +
                       7*r["Vendors"])
    satisfaction = clamp(85 - service_penalty, 0, 100)
    # All coefficients illustrative; nonlinearity captures accelerating harm.
    demand_drag = (
        0.72 * r["Discounts"]**1.1 +
        0.38 * r["Marketing & promotions"]**1.1 +
        0.22 * r["Vendors"]**1.5 +
        0.13 * r["Logistics"]**1.5 +
        0.12 * r["Technology"]**1.5 +
        0.08 * r["Warehousing"]**1.5 +
        0.05 * r["Payment gateways"]**1.5
    )
    orders1 = clamp(100 * math.exp(-demand_drag), 5, 140)
    revenue1 = orders1  # constant net revenue per fulfilled order in this model
    retention = clamp(0.85 - 0.007 * max(0, 85-satisfaction) -
                      0.11*r["Discounts"] - 0.05*r["Vendors"], 0.30, 0.95)
    # Period 2 captures retention effects and reduced customer acquisition.
    orders2 = clamp(orders1 * (1.12 * (retention/0.85) ** 0.75) *
                    (1 - 0.15 * r["Marketing & promotions"]), 5, 150)
    revenue2 = orders2
    def period_costs(volume):
        factor = volume / 100.0
        return {name: base * (1-r[name]) *
                (VARIABLE_SHARES[name] * factor + (1-VARIABLE_SHARES[name]))
                for name, base in BASE_COSTS.items()}
    c1 = period_costs(orders1)
    c2 = period_costs(orders2)
    # A small second-period deterioration in returns/failed transactions when
    # packaging, logistics or payments are compromised (additional real costs).
    c2["Others"] += revenue2 * (0.025*r["Packaging"] +
                                  0.015*r["Logistics"] +
                                  0.015*r["Payment gateways"])
    cost1, cost2 = sum(c1.values()), sum(c2.values())
    profit1, profit2 = revenue1-cost1, revenue2-cost2
    cash_end = rules["opening_cash"] + profit1 + profit2
    tests = {
        "Period 1 revenue": revenue1 >= rules["min_revenue_p1"],
        "Period 1 loss": profit1 >= -rules["max_loss_p1"],
        "Customer satisfaction": satisfaction >= rules["min_satisfaction"],
        "Period 2 revenue": revenue2 >= rules["min_revenue_p2"],
        "Cash survival": cash_end >= 0,
    }
    # Valuation proxy, only for classroom discussion. Revenue multiple depends
    # on growth, margin and retention, not mechanically on revenue alone.
    growth = revenue2/revenue1 - 1
    margin = profit2/max(revenue2, 0.01)
    multiple = clamp(2.4 + 2.0*(growth-0.10) + 1.2*(retention-0.85) +
                     1.0*(margin+0.35), 0.5, 4.0)
    valuation = revenue2 * multiple
    return {
        "orders_p1": orders1, "orders_p2": orders2,
        "revenue_p1": revenue1, "revenue_p2": revenue2,
        "cost_p1": cost1, "cost_p2": cost2,
        "profit_p1": profit1, "profit_p2": profit2,
        "costs_p1": c1, "costs_p2": c2,
        "satisfaction": satisfaction, "retention": retention,
        "growth_p2": growth, "cash_end": cash_end,
        "valuation_multiple": multiple, "valuation_proxy": valuation,
        "investor_tests": tests, "investor_approved": all(tests.values()),
        "constraints_met": sum(tests.values()),
        "cumulative_profit": profit1 + profit2,
    }
