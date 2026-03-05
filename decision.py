"""
The Decision class represents the monthly decisions made by the user that affect business performance.
"""


class Decision:
    """
    Represents one month of business decisions.
    """

    def __init__(
        self,
        business_id,
        year,
        month,
        price_change_pct,
        marketing_spend,
        staff_cost_adjustment,
        waste_reduction_pct,
        inventory_tightness,
    ):
        """
        Create a Decision object for one month.
        """

        self.business_id = business_id
        self.year = int(year)
        self.month = int(month)
        self.price_change_pct = float(price_change_pct)
        self.marketing_spend = float(marketing_spend)
        self.staff_cost_adjustment = float(staff_cost_adjustment)
        self.waste_reduction_pct = float(waste_reduction_pct)
        self.inventory_tightness = float(inventory_tightness)

    def print_summary(self):
        """
        Print a simple summary of the decision.
        """
        print("Business ID:", self.business_id)
        print("Year:", self.year)
        print("Month:", self.month)
        print("Price Change %:", self.price_change_pct)
        print("Marketing Spend:", self.marketing_spend)
        print("Staff Cost Adjustment:", self.staff_cost_adjustment)
        print("Waste Reduction %:", self.waste_reduction_pct)
        print("Inventory Tightness:", self.inventory_tightness)
