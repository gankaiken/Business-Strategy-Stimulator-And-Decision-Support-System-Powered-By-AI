"""
The Company class represents a small business and stores
all baseline financial information such as sales, costs and starting cash
"""


class Company:
    """
    Represents a small business (restaurant or grocery).
    """

    def __init__(
        self,
        business_id,
        business_type,
        starting_cash,
        baseline_sales,
        baseline_cogs,
        rent,
        staff_cost,
        utilities,
        subscriptions,
        loan_payment,
        other_fixed,
    ):
        """
        Create a Company object with baseline information.
        """

        self.business_id = business_id
        self.business_type = business_type
        self.starting_cash = float(starting_cash)

        self.baseline_sales = float(baseline_sales)
        self.baseline_cogs = float(baseline_cogs)

        self.rent = float(rent)
        self.staff_cost = float(staff_cost)
        self.utilities = float(utilities)
        self.subscriptions = float(subscriptions)
        self.loan_payment = float(loan_payment)
        self.other_fixed = float(other_fixed)

    def calculate_fixed_costs(self):
        """
        Calculate total fixed costs for one month.
        @return float
        """
        return (
            self.rent
            + self.staff_cost
            + self.utilities
            + self.subscriptions
            + self.loan_payment
            + self.other_fixed
        )

    def get_basic_info(self):
        """
        Return basic business info as a dictionary.
        """
        return {
            "business_id": self.business_id,
            "business_type": self.business_type,
            "starting_cash": self.starting_cash,
        }

    def print_summary(self):
        """
        Print a simple summary of the business.
        """
        print("Business ID:", self.business_id)
        print("Business Type:", self.business_type)
        print("Starting Cash:", self.starting_cash)
        print("Baseline Sales:", self.baseline_sales)
        print("Baseline COGS:", self.baseline_cogs)
        print("Total Fixed Costs:", self.calculate_fixed_costs())
