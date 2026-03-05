"""
The Market class represents external market behaviour that affects sales, such as:
- price sensitivity (price elasticity)
- marketing impact
- seasonality effects
"""

import math


class Market:
    """
    Represents market behaviour for a business.
    """

    def __init__(self, price_elasticity, marketing_effectiveness, seasonality_strength):
        """
        Create a Market object.

        @param price_elasticity - how sensitive customers are to price changes
        @param marketing_effectiveness - how effective marketing spend is
        @param seasonality_strength - strength of seasonal changes
        """

        self.price_elasticity = float(price_elasticity)
        self.marketing_effectiveness = float(marketing_effectiveness)
        self.seasonality_strength = float(seasonality_strength)

    def calculate_price_effect(self, price_change_pct):
        """
        Calculate how price changes affect demand.

        @param price_change_pct - price change as a decimal (e.g. 0.05 = +5%)
        @return float - demand multiplier due to price change
        """
        effect = 1 + (self.price_elasticity * price_change_pct)
        if effect < 0.3:
            effect = 0.3
        return effect

    def calculate_marketing_effect(self, marketing_spend):
        """
        Calculate how marketing spend affects demand.

        @param marketing_spend - amount spent on marketing
        @return float - demand multiplier due to marketing
        """
        if marketing_spend <= 0:
            return 1.0

        effect = 1 + (math.log(marketing_spend + 1) * self.marketing_effectiveness)
        return effect

    def calculate_seasonality_effect(self, month):
        """
        Calculate seasonal effect based on month.

        @param month - month number (1 to 12)
        @return float - seasonal demand multiplier
        """
        effect = 1 + (self.seasonality_strength * math.sin(month))
        return effect

    def calculate_total_demand_effect(self, price_change_pct, marketing_spend, month):
        """
        Combine price, marketing, and seasonality effects.

        @param price_change_pct - price change percentage
        @param marketing_spend - marketing spend
        @param month - current month
        @return float - total demand multiplier
        """
        price_effect = self.calculate_price_effect(price_change_pct)
        marketing_effect = self.calculate_marketing_effect(marketing_spend)
        seasonality_effect = self.calculate_seasonality_effect(month)

        total_effect = price_effect * marketing_effect * seasonality_effect
        return total_effect

    def print_summary(self):
        """
        Print a simple summary of market settings.

        @return None
        """
        print("Market Settings")
        print("Price Elasticity:", self.price_elasticity)
        print("Marketing Effectiveness:", self.marketing_effectiveness)
        print("Seasonality Strength:", self.seasonality_strength)


def create_default_market(business_type):
    """
    Create default market settings based on business type.

    @param business_type - type of business (restaurant or grocery)
    @return Market - Market object with default values
    """
    if business_type == "restaurant":
        return Market(
            price_elasticity=-1.1,
            marketing_effectiveness=0.0008,
            seasonality_strength=0.06,
        )
    else:
        return Market(
            price_elasticity=-0.6,
            marketing_effectiveness=0.0004,
            seasonality_strength=0.03,
        )
