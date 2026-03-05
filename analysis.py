"""
SME decision support logic.
"""

import math


class SMEAdvisor:
    """
    Provides analysis and recommendations based on simulation outcomes.
    """

    def get_benchmarks(self, business_type):
        """
        Return benchmark ranges based on business type.
        @param business_type - 'restaurant' or 'grocery'
        @return dict
        """
        if business_type == "restaurant":
            return {
                "gross_margin_min": 0.55,
                "rent_ratio_max": 0.18,
                "staff_ratio_max": 0.35,
            }
        else:
            return {
                "gross_margin_min": 0.18,
                "rent_ratio_max": 0.12,
                "staff_ratio_max": 0.20,
            }

    def calculate_gross_margin(self, sales, cogs):
        if sales <= 0:
            return 0.0
        return max(0.0, (sales - cogs) / sales)

    def calculate_runway(self, cash_end, monthly_loss):
        if monthly_loss <= 0:
            return math.inf
        if cash_end <= 0:
            return 0.0
        return cash_end / monthly_loss

    def get_health_flag(self, runway):
        if runway == math.inf:
            return "GREEN"
        if runway < 1.5:
            return "RED"
        if runway < 4:
            return "YELLOW"
        return "GREEN"

    def analyse_one_month(self, company, month_data):
        """
        Analyse one month of results.
        @return list (enriched row)
        """
        year, month, sales, cogs, fixed_costs, marketing, profit, cash_end = month_data

        sales = float(sales)
        cogs = float(cogs)
        fixed_costs = float(fixed_costs)
        profit = float(profit)
        cash_end = float(cash_end)

        gross_margin = self.calculate_gross_margin(sales, cogs)
        monthly_loss = abs(profit) if profit < 0 else 0
        runway = self.calculate_runway(cash_end, monthly_loss)
        health = self.get_health_flag(runway)

        rent_ratio = company.rent / sales if sales > 0 else 0
        staff_ratio = company.staff_cost / sales if sales > 0 else 0

        benchmarks = self.get_benchmarks(company.business_type)

        causes = []
        suggestions = []
        impact_scores = {}

        # Initialise
        gap = 0.0

        # Break-even
        if gross_margin > 0:
            break_even_sales = fixed_costs / gross_margin
            gap = break_even_sales - sales
            if gap > 500:
                be_status = f"Below break-even by ~RM{gap:,.0f}"
            elif gap < -500:
                be_status = "Above break-even"
            else:
                be_status = "Around break-even"
        else:
            be_status = "Break-even not calculable"

        # LOSS CASE
        if profit < 0:
            readiness = "Not Ready"

            if gross_margin < benchmarks["gross_margin_min"]:
                causes.append("Low gross margin")
                suggestions.append("Reduce waste or adjust pricing")
                impact_scores["margin"] = sales * (
                    benchmarks["gross_margin_min"] - gross_margin
                )

            if rent_ratio > benchmarks["rent_ratio_max"]:
                causes.append("High rent burden")
                suggestions.append("Negotiate rent or grow revenue")
                impact_scores["rent"] = company.rent

            if staff_ratio > benchmarks["staff_ratio_max"]:
                causes.append("High staff cost")
                suggestions.append("Improve staffing efficiency")
                impact_scores["staff"] = company.staff_cost

            if gap > 0:
                causes.append("Sales below break-even")
                impact_scores["sales_gap"] = gap

            if runway != math.inf and runway < 3:
                causes.append("Critical cash runway")
                suggestions.append("Freeze non-essential spending")

        # PROFIT CASE
        else:
            causes.append("Business is profitable")

            if runway >= 6 or runway == math.inf:
                readiness = "Ready to Expand Carefully"
            else:
                readiness = "Profitable but Cash-Constrained"

            suggestions.append("Build cash buffer before expanding")
            impact_scores["profit"] = profit

        root_cause = (
            max(impact_scores, key=impact_scores.get) if impact_scores else "None"
        )
        summary = generate_summary(root_cause, profit)
        cause_scores_str = "|".join([f"{k}:{v:.2f}" for k, v in impact_scores.items()])

        return [
            company.business_id,  # 0
            str(year),  # 1
            str(month),  # 2
            str(sales),  # 3
            str(cogs),  # 4
            str(fixed_costs),  # 5
            str(marketing),  # 6
            str(profit),  # 7
            str(cash_end),  # 8
            str(gross_margin),  # 9
            str(runway if runway != math.inf else "Not Losing Money"),  # 10
            health,  # 11
            "|".join(causes),  # 12
            "|".join(suggestions),  # 13
            be_status,  # 14
            root_cause,  # 15
            summary,  # 16
            readiness,  # 17
            cause_scores_str,  # 18
        ]

    def analyse_year(self, company, year_results):
        return [self.analyse_one_month(company, r) for r in year_results]


def explain_root_cause(root_cause):
    """
    Convert internal root cause codes into user-friendly explanations.
    """
    explanations = {
        "sales_gap": "Sales are too low to cover fixed costs (below break-even level)",
        "margin": "Profit margin is too low (cost of goods is too high)",
        "staff": "Staff costs are too high relative to sales",
        "rent": "Rent is too high relative to sales",
        "profit": "Business is generating sufficient profit",
        "None": "No dominant issue detected",
    }
    return explanations.get(root_cause, "Unclear root cause")


def generate_summary(root_cause, profit):
    """
    Generate a human-readable summary based on root cause.
    """
    if profit >= 0:
        return "Profitable month with positive operating performance"

    summaries = {
        "sales_gap": "Loss-making month because sales are below break-even level",
        "margin": "Loss-making month due to low profit margin",
        "staff": "Loss-making month driven by high staff costs",
        "rent": "Loss-making month driven by high rent costs",
    }

    return summaries.get(root_cause, "Loss-making month due to multiple cost pressures")
