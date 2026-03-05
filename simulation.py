"""
This file contains the simulation logic for the Business Strategy Simulator.
"""

import random
from decision import Decision
from sorting import calculate_sum, insertion_sort


class BusinessSimulator:
    """
    Simulates business performance over time.
    """

    def __init__(self, seed):
        """
        Initialise the simulator with a random seed.
        @param seed - integer seed value for reproducible randomness
        @return None
        """
        self.seed = int(seed)
        random.seed(self.seed)

    def simulate_one_month(self, company, market, decision, cash_start):
        """
        Simulate one month of business operations.
        @param company - Company object containing baseline business data
        @param market - Market object containing market behaviour
        @param decision - Decision object for the month
        @param cash_start - cash available at the start of the month
        @return list - [sales, cogs, fixed_costs, profit, cash_end]
        """

        base_sales = company.baseline_sales
        demand_multiplier = market.calculate_total_demand_effect(
            decision.price_change_pct,
            decision.marketing_spend,
            decision.month,
        )
        noise = random.uniform(0.94, 1.06)
        sales = base_sales * demand_multiplier * noise
        if company.baseline_sales > 0:
            cogs_ratio = company.baseline_cogs / company.baseline_sales
        else:
            cogs_ratio = 0.0

        waste_factor = 1 - decision.waste_reduction_pct
        if waste_factor < 0.7:
            waste_factor = 0.7

        spoilage_factor = 1.0
        if company.business_type == "grocery":
            spoilage_factor = 1.0 + (0.08 * (1.0 - decision.inventory_tightness))

        cogs = sales * cogs_ratio * waste_factor * spoilage_factor

        fixed_costs = company.calculate_fixed_costs() + decision.staff_cost_adjustment
        if fixed_costs < 0:
            fixed_costs = 0.0

        profit = sales - cogs - fixed_costs - decision.marketing_spend
        cash_end = cash_start + profit
        return [sales, cogs, fixed_costs, profit, cash_end]

    def simulate_12_months(self, company, market, decisions):
        """
        Simulate a full year (12 months) of business performance.
        @param company - Company object
        @param market - Market object
        @param decisions - list of Decision objects
        @return list - list of monthly simulation results
        """

        results = []
        cash = company.starting_cash

        decisions.sort(key=lambda d: d.month)

        for decision in decisions:
            month_result = self.simulate_one_month(company, market, decision, cash)

            sales, cogs, fixed_costs, profit, cash_end = month_result

            results.append(
                [
                    decision.year,
                    decision.month,
                    sales,
                    cogs,
                    fixed_costs,
                    decision.marketing_spend,
                    profit,
                    cash_end,
                ]
            )

            cash = cash_end

        return results

    def simulate_months(self, company, market, decisions, starting_cash=100_000):
        """
        Simulate a variable number of months for a company using a list of Decision objects.
        Tracks cash across months.
        """
        results = []
        cash = starting_cash

        for decision in decisions:
            month_result = self.simulate_one_month(
                company, market, decision, cash_start=cash
            )

            if month_result is None:
                return None

            results.append(month_result)
            cash = month_result[4]  # cash_end for next month

        return results

    def project_linear_trend(self, past_results, key_index, num_future=6):
        """
        Project future values using a simple linear trend.
        @param past_results - list of past monthly results
        @param key_index - index of the value to project (e.g. profit, sales)
        @param num_future - number of future months to project
        @return list - list of (month, projected_value)
        """

        if len(past_results) < 2:
            last_month = past_results[-1][1]
            last_value = past_results[-1][key_index]
            return [(last_month + i + 1, last_value) for i in range(num_future)]

        months = [r[1] for r in past_results]
        values = [float(r[key_index]) for r in past_results]

        x1, x2 = months[0], months[-1]
        y1, y2 = values[0], values[-1]

        if x2 == x1:
            slope = 0.0
        else:
            slope = (y2 - y1) / (x2 - x1)

        intercept = y1 - slope * x1

        projections = []
        last_month = months[-1]
        for i in range(1, num_future + 1):
            m = last_month + i
            v = intercept + slope * m
            projections.append((m, v))

        return projections

    def prepare_full_year_decisions(self, decisions, year, business_id):
        """
        Ensure decisions cover all 12 months.
        @param decisions - list of Decision objects
        @param year - simulation year
        @param business_id - business identifier
        @return list of 12 Decision objects
        """

        if not decisions:
            raise ValueError("No decisions provided for simulation.")
        decisions = sorted(decisions, key=lambda d: d.month)

        full_decisions = []
        last_decision = None

        for month in range(1, 13):
            match = next((d for d in decisions if d.month == month), None)

            if match:
                full_decisions.append(match)
                last_decision = match
            else:
                reused = Decision(
                    business_id=business_id,
                    year=year,
                    month=month,
                    price_change_pct=last_decision.price_change_pct,
                    marketing_spend=last_decision.marketing_spend,
                    staff_cost_adjustment=last_decision.staff_cost_adjustment,
                    waste_reduction_pct=last_decision.waste_reduction_pct,
                    inventory_tightness=last_decision.inventory_tightness,
                )
                full_decisions.append(reused)

        return full_decisions

    def simulate_one_year_full(self, company, market, decisions):
        """
        Run a full-year simulation and return risk metrics for Monte Carlo.
        """

        cash = company.starting_cash
        total_profit = 0.0

        # Track minimum runway ONLY for months where u r actually losing money
        min_runway_numeric = float("inf")

        red_months = 0
        bankrupt = False

        for decision in decisions:
            sales, cogs, fixed_costs, profit, cash_end = self.simulate_one_month(
                company, market, decision, cash
            )

            total_profit += profit
            monthly_loss = max(0.0, -profit)

            if monthly_loss > 0:
                runway = cash_end / monthly_loss if cash_end > 0 else 0.0
                if runway < min_runway_numeric:
                    min_runway_numeric = runway

                if runway < 1.5:
                    red_months += 1

            if cash_end <= 0:
                bankrupt = True
                cash = 0.0
                break

            cash = cash_end

        min_runway = (
            "Stable" if min_runway_numeric == float("inf") else min_runway_numeric
        )

        return {
            "ending_cash": cash,
            "total_profit": total_profit,
            "min_runway": min_runway,
            "red_months": red_months,
            "bankrupt": bankrupt,
        }

    def monte_carlo_full_year(
        self,
        company,
        market,
        decisions,
        business_id,
        year,
        num_runs=500,
        verbose=True,
        progress_callback=None,
    ):
        """
        Run Monte Carlo simulation for a full year.
        """

        decisions = self.prepare_full_year_decisions(decisions, year, business_id)

        all_results = []

        if verbose:
            print(
                f"Running Monte Carlo risk analysis ({num_runs} full-year simulations)..."
            )

        base_seed = int(self.seed)

        for i in range(num_runs):
            if progress_callback:
                try:
                    progress_callback(i + 1, num_runs)
                except TypeError:
                    progress_callback(i + 1)

            if verbose and (i + 1) % 100 == 0:
                print(f"  {i + 1}/{num_runs} runs completed")

            random.seed(base_seed + i)
            run_metrics = self.simulate_one_year_full(company, market, decisions)
            all_results.append(run_metrics)

        random.seed(base_seed)

        ending_cash_list = [r.get("ending_cash", 0) for r in all_results]
        profit_list = [r.get("total_profit", 0) for r in all_results]

        runway_numeric = []
        stable_count = 0
        for r in all_results:
            v = r.get("min_runway")
            if isinstance(v, str) and v.lower() == "stable":
                stable_count += 1
            else:
                try:
                    runway_numeric.append(float(v))
                except:
                    pass

        def calc_stats(values):
            if not values:
                return {}

            values = insertion_sort(values)
            n = len(values)

            mean = calculate_sum(values) / n
            median = (
                values[n // 2]
                if n % 2 == 1
                else (values[n // 2 - 1] + values[n // 2]) / 2
            )

            p5 = values[int(0.05 * (n - 1))]
            p95 = values[int(0.95 * (n - 1))]

            variance = calculate_sum((x - mean) ** 2 for x in values) / n
            std = variance**0.5

            return {
                "mean": mean,
                "median": median,
                "min": min(values),
                "max": max(values),
                "p5": p5,
                "p95": p95,
                "std": std,
            }

        bankrupt_count = calculate_sum(1 for r in all_results if r.get("bankrupt"))
        positive_profit_count = calculate_sum(
            1 for r in all_results if r.get("total_profit", 0) > 0
        )
        red_months_total = calculate_sum(r.get("red_months", 0) for r in all_results)

        stats = {
            "ending_cash": calc_stats(ending_cash_list),
            "total_profit": calc_stats(profit_list),
            "min_runway": calc_stats(runway_numeric),
            "stable_runway_prob": (
                (stable_count / num_runs * 100) if num_runs > 0 else 0.0
            ),
            "bankruptcy_prob": (
                (bankrupt_count / num_runs * 100) if num_runs > 0 else 0.0
            ),
            "positive_profit_prob": (
                (positive_profit_count / num_runs * 100) if num_runs > 0 else 0.0
            ),
            "avg_red_months": (red_months_total / num_runs) if num_runs > 0 else 0.0,
        }

        return all_results, stats
