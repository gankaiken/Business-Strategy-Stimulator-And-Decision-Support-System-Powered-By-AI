"""
Sensitivity analysis tests which business decision has the biggest impact on profit by slightly changing one
decision at a time and re-running the simulation.
"""

from decision import Decision
from sorting import insertion_sort


def run_sensitivity(
    month,
    base_decision,
    company,
    market,
    simulator,
    cash_start,
):
    """
    Test which decision lever has the biggest impact on profit
    by applying small changes one at a time.
    """

    results = []

    _, _, _, base_profit, _ = simulator.simulate_one_month(
        company, market, base_decision, cash_start
    )

    test_changes = [
        ("price_change_pct", base_decision.price_change_pct + 0.02),
        ("marketing_spend", base_decision.marketing_spend + 300),
        ("staff_cost_adjustment", base_decision.staff_cost_adjustment - 200),
        ("waste_reduction_pct", base_decision.waste_reduction_pct + 0.05),
    ]

    for field, new_value in test_changes:
        # Clone decision
        test_decision = Decision(
            base_decision.business_id,
            base_decision.year,
            month,
            base_decision.price_change_pct,
            base_decision.marketing_spend,
            base_decision.staff_cost_adjustment,
            base_decision.waste_reduction_pct,
            base_decision.inventory_tightness,
        )

        setattr(test_decision, field, new_value)
        _, _, _, new_profit, _ = simulator.simulate_one_month(
            company, market, test_decision, cash_start
        )

        results.append(
            {
                "lever": field,
                "profit_change": new_profit - base_profit,
            }
        )

    insertion_sort(results, key_func=lambda x: x["profit_change"], reverse=True)

    return results
