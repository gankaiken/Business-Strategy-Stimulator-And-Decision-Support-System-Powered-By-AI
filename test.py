"""
Unit tests for Business Strategy Simulator core functionality.
Tests simulation, analysis, and optimization components.
"""

import unittest
from company import Company
from decision import Decision
from market import Market, create_default_market
from simulation import BusinessSimulator
from analysis import SMEAdvisor
from sorting import insertion_sort, calculate_sum, find_max


class TestSimulation(unittest.TestCase):
    """Test core simulation logic."""

    def setUp(self):
        """Create test company and market."""
        self.company = Company(
            business_id="test_cafe",
            business_type="restaurant",
            starting_cash=50000,
            baseline_sales=45000,
            baseline_cogs=18000,
            rent=8000,
            staff_cost=12000,
            utilities=1500,
            subscriptions=500,
            loan_payment=2000,
            other_fixed=1000,
        )
        self.market = create_default_market("restaurant")
        self.simulator = BusinessSimulator(seed=42)

    def test_fixed_costs_calculation(self):
        """Test total fixed costs sum correctly."""
        expected = 8000 + 12000 + 1500 + 500 + 2000 + 1000
        self.assertEqual(self.company.calculate_fixed_costs(), expected)

    def test_simulate_one_month_returns_valid_result(self):
        """Test single month simulation produces valid output."""
        decision = Decision("test_cafe", 2024, 1, 0.0, 1500, 0, 0.05, 0.8)
        result = self.simulator.simulate_one_month(
            self.company, self.market, decision, 50000
        )

        self.assertEqual(len(result), 5)  # [sales, cogs, fixed, profit, cash]
        self.assertGreater(result[0], 0)  # Sales > 0
        self.assertGreater(result[1], 0)  # COGS > 0
        self.assertIsInstance(result[4], float)  # Cash is float

    def test_baseline_scenario_is_profitable(self):
        """Test that baseline settings produce profit."""
        decision = Decision("test_cafe", 2024, 1, 0.0, 1500, 0, 0.05, 0.8)
        result = self.simulator.simulate_one_month(
            self.company, self.market, decision, 50000
        )

        profit = result[3]
        self.assertGreater(profit, 0, "Baseline scenario should be profitable")


class TestAnalysis(unittest.TestCase):
    """Test analysis and diagnostics."""

    def setUp(self):
        """Create test advisor and company."""
        self.advisor = SMEAdvisor()
        self.company = Company(
            "test_cafe",
            "restaurant",
            50000,
            45000,
            18000,
            8000,
            12000,
            1500,
            500,
            2000,
            1000,
        )

    def test_gross_margin_calculation(self):
        """Test gross margin formula."""
        margin = self.advisor.calculate_gross_margin(45000, 18000)
        self.assertAlmostEqual(margin, 0.6, places=2)

    def test_gross_margin_zero_sales(self):
        """Test gross margin with zero sales."""
        margin = self.advisor.calculate_gross_margin(0, 18000)
        self.assertEqual(margin, 0.0)

    def test_runway_calculation(self):
        """Test runway calculation logic."""
        runway = self.advisor.calculate_runway(30000, 5000)
        self.assertEqual(runway, 6.0)

    def test_runway_infinite_when_profitable(self):
        """Test runway is infinite when no loss."""
        runway = self.advisor.calculate_runway(50000, 0)
        self.assertEqual(runway, float("inf"))

    def test_health_flag_green(self):
        """Test GREEN health flag for safe runway."""
        health = self.advisor.get_health_flag(7.5)
        self.assertEqual(health, "GREEN")

    def test_health_flag_yellow(self):
        """Test YELLOW health flag for moderate runway."""
        health = self.advisor.get_health_flag(3.0)
        self.assertEqual(health, "YELLOW")

    def test_health_flag_red(self):
        """Test RED health flag for critical runway."""
        health = self.advisor.get_health_flag(1.0)
        self.assertEqual(health, "RED")


class TestSorting(unittest.TestCase):
    """Test custom sorting and utility functions."""

    def test_insertion_sort_ascending(self):
        """Test insertion sort in ascending order."""
        data = [5, 2, 8, 1, 9]
        result = insertion_sort(data.copy())
        self.assertEqual(result, [1, 2, 5, 8, 9])

    def test_insertion_sort_descending(self):
        """Test insertion sort in descending order."""
        data = [5, 2, 8, 1, 9]
        result = insertion_sort(data.copy(), reverse=True)
        self.assertEqual(result, [9, 8, 5, 2, 1])

    def test_insertion_sort_with_key_function(self):
        """Test insertion sort with custom key."""
        data = [{"val": 5}, {"val": 2}, {"val": 8}]
        result = insertion_sort(data.copy(), key_func=lambda x: x["val"])
        self.assertEqual([r["val"] for r in result], [2, 5, 8])

    def test_calculate_sum(self):
        """Test custom sum calculation."""
        total = calculate_sum([1, 2, 3, 4, 5])
        self.assertEqual(total, 15)

    def test_find_max(self):
        """Test finding maximum value."""
        maximum = find_max([3, 7, 2, 9, 1])
        self.assertEqual(maximum, 9)

    def test_find_max_with_key(self):
        """Test finding max with custom key."""
        data = [{"val": 5}, {"val": 12}, {"val": 3}]
        maximum = find_max(data, key_func=lambda x: x["val"])
        self.assertEqual(maximum["val"], 12)


class TestMarket(unittest.TestCase):
    """Test market behavior and demand effects."""

    def setUp(self):
        """Create test market."""
        self.market = Market(
            price_elasticity=-1.1,
            marketing_effectiveness=0.0008,
            seasonality_strength=0.06,
        )

    def test_price_effect_increase(self):
        """Test demand decreases when price increases."""
        effect = self.market.calculate_price_effect(0.10)  # +10% price
        self.assertLess(effect, 1.0, "Demand should decrease with price increase")

    def test_price_effect_decrease(self):
        """Test demand increases when price decreases."""
        effect = self.market.calculate_price_effect(-0.10)  # -10% price
        self.assertGreater(effect, 1.0, "Demand should increase with price decrease")

    def test_marketing_effect_positive(self):
        """Test marketing spend increases demand."""
        effect = self.market.calculate_marketing_effect(2000)
        self.assertGreater(effect, 1.0, "Marketing should boost demand")

    def test_marketing_effect_zero(self):
        """Test zero marketing has no effect."""
        effect = self.market.calculate_marketing_effect(0)
        self.assertEqual(effect, 1.0)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
