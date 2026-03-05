"""
This file defines the MonthlyResult class.
The MonthlyResult class stores the outcome of the simulation
for one month, including financial results and analysis.
"""


class MonthlyResult:
    """
    Represents the simulation result for one month.
    """

    def __init__(
        self,
        business_id,
        year,
        month,
        sales,
        cogs,
        fixed_costs,
        marketing_spend,
        profit,
        cash_end,
        gross_margin,
        runway_months,
        health_flag,
        causes,
        suggestions,
    ):
        """
        Create a MonthlyResult object.
        @param business_id - unique business identifier
        @param year - simulation year
        @param month - month number (1 to 12)
        @param sales - total sales for the month
        @param cogs - cost of goods sold
        @param fixed_costs - total fixed costs
        @param marketing_spend - marketing spend for the month
        @param profit - profit or loss for the month
        @param cash_end - cash balance at end of month
        @param gross_margin - gross margin for the month
        @param runway_months - estimated months the business can survive
        @param health_flag - business health status (GREEN/YELLOW/RED)
        @param causes - list or string of reasons
        @param suggestions - list or string of actions
        @return None
        """
        self.business_id = business_id
        self.year = int(year)
        self.month = int(month)
        self.sales = float(sales)
        self.cogs = float(cogs)
        self.fixed_costs = float(fixed_costs)
        self.marketing_spend = float(marketing_spend)
        self.profit = float(profit)
        self.cash_end = float(cash_end)
        self.gross_margin = float(gross_margin)
        self.runway_months = runway_months
        self.health_flag = health_flag

        self.causes = causes.split("|") if isinstance(causes, str) else causes
        self.suggestions = (
            suggestions.split("|") if isinstance(suggestions, str) else suggestions
        )

    def is_profitable(self):
        """
        Check if the business made profit this month.
        @return bool - True if profit >= 0
        """
        return self.profit >= 0

    def print_summary(self):
        """
        Print a simple summary of the monthly result.
        @return None
        """
        print(f"\nMonth {self.month} Summary")
        print("Sales:", self.sales)
        print("Profit:", self.profit)
        print("Cash End:", self.cash_end)
        print("Runway (months):", self.runway_months)
        print("Health:", self.health_flag)

        print("Causes:")
        for cause in self.causes:
            print("-", cause)

        print("Suggestions:")
        for suggestion in self.suggestions:
            print("-", suggestion)
