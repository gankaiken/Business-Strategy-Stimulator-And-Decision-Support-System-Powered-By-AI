"""
This file handles data visualisation for the simulator.
"""

import os
from datetime import datetime
from company import Company
from schemas import HISTORY_CSV_TEMPLATE
from data_io import read_csv, get_goal
from sorting import insertion_sort
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Patch, Rectangle
from matplotlib.lines import Line2D
import numpy as np
import calendar


class Visualizer:
    """
    Creates graphs to visualise business performance.
    """

    def __init__(self):
        """
        Create a Visualizer object.
        """
        pass

    def plot_cash_over_time(self, results):
        """
        Plot cash balance at the end of each month.
        @param results - analysed result rows
        @return None
        """
        months = [int(r[2]) for r in results]
        cash = [float(r[8]) for r in results]

        plt.figure()
        plt.plot(months, cash, marker="o")
        plt.xlabel("Month")
        plt.ylabel("Cash Balance (RM)")
        plt.title("Cash Balance Over Time")
        plt.grid(True)
        plt.show()

    def plot_profit_over_time(self, results):
        """
        Plot monthly profit or loss.
        @param results - analysed result rows
        @return None
        """
        months = [int(r[2]) for r in results]
        profit = [float(r[7]) for r in results]

        plt.figure()
        plt.plot(months, profit, marker="o")
        plt.axhline(y=0, linestyle="--")
        plt.xlabel("Month")
        plt.ylabel("Profit / Loss (RM)")
        plt.title("Monthly Profit or Loss")
        plt.grid(True)
        plt.show()

    def plot_sales_over_time(self, results):
        """
        Plot monthly sales trend.
        @param results - analysed result rows
        @return None
        """
        months = [int(r[2]) for r in results]
        sales = [float(r[3]) for r in results]

        plt.figure()
        plt.plot(months, sales, marker="o")
        plt.xlabel("Month")
        plt.ylabel("Sales (RM)")
        plt.title("Sales Over Time")
        plt.grid(True)
        plt.show()

    def plot_cost_breakdown(self, results, company):
        """
        Plot average cost breakdown using a pie chart.
        @param results - analysed result rows
        @param company - Company object
        @return None
        """
        avg_cogs = sum(float(r[4]) for r in results) / len(results)
        avg_marketing = sum(float(r[6]) for r in results) / len(results)

        fixed_costs = (
            company.rent
            + company.staff_cost
            + company.utilities
            + company.subscriptions
            + company.loan_payment
            + company.other_fixed
        )

        labels = ["COGS", "Fixed Costs", "Marketing"]
        values = [avg_cogs, fixed_costs, avg_marketing]

        plt.figure()
        plt.pie(values, labels=labels, autopct="%1.1f%%")
        plt.title("Average Cost Breakdown")
        plt.show()

    def plot_root_causes(self, results):
        """
        Plot frequency of root causes across months.
        @param results - analysed result rows
        @return None
        """
        cause_count = {}

        for r in results:
            root = r[15]  # root_cause
            cause_count[root] = cause_count.get(root, 0) + 1

        labels = list(cause_count.keys())
        values = list(cause_count.values())

        plt.figure()
        plt.bar(labels, values)
        plt.xlabel("Root Cause")
        plt.ylabel("Number of Months")
        plt.title("Main Root Causes of Performance")
        plt.xticks(rotation=30)
        plt.grid(True, axis="y")
        plt.show()

    def plot_runway_progress(self, business_id):
        """
        Plot runway progress over time from history data.
        @param business_id - business identifier
        @return None
        """
        file_path = HISTORY_CSV_TEMPLATE.format(business_id=business_id)

        if not os.path.exists(file_path):
            print("No history data available.")
            return

        rows = read_csv(file_path)
        if not rows:
            return

        dates = []
        runways = []

        for row in rows:
            try:
                dates.append(datetime.fromisoformat(row[1]))
                val = row[4]
                runways.append(12 if val == "Stable" else float(val))
            except:
                continue

        plt.figure(figsize=(10, 4))
        plt.plot(dates, runways, marker="o")
        plt.axhline(y=3, linestyle="--", label="Critical")
        plt.axhline(y=6, linestyle="--", label="Caution")

        goal = get_goal(business_id)
        if goal:
            plt.axhline(y=goal, label="Goal", linewidth=2)

        plt.title("Runway Progress Over Time")
        plt.xlabel("Date")
        plt.ylabel("Runway (Months)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def plot_scenario_comparison(self, scenarios):
        """
        Compare scenarios by total profit.
        @param scenarios - list of scenario dictionaries
        @return None
        """
        names = [s["scenario_name"] for s in scenarios]
        profits = [float(s["total_profit"]) for s in scenarios]

        plt.figure()
        plt.bar(names, profits)
        plt.xlabel("Scenario")
        plt.ylabel("Total Profit (RM)")
        plt.title("Scenario Profit Comparison")
        plt.grid(True, axis="y")
        plt.show()

    def plot_cash_histogram(
        self, ending_cash_list, bins=20, title="Monte Carlo: Ending Cash Distribution"
    ):
        """
        Matplotlib histogram for Monte Carlo ending cash.
        """

        if not ending_cash_list:
            print("No Monte Carlo results to plot.")
            return

        bankrupt_count = sum(1 for v in ending_cash_list if v <= 0)
        total = len(ending_cash_list)
        bankrupt_pct = (bankrupt_count / total * 100) if total > 0 else 0.0

        positives = [v for v in ending_cash_list if v > 0]

        plt.figure()
        if positives:
            plt.hist(positives, bins=bins)
            plt.xlabel("Ending Cash (RM)")
            plt.ylabel("Frequency")
            plt.title(
                f"{title}\nBankruptcy: {bankrupt_count}/{total} ({bankrupt_pct:.1f}%)"
            )
        else:
            plt.title(
                f"{title}\nAll simulations ended in bankruptcy ({bankrupt_count}/{total})"
            )
            plt.xlabel("Ending Cash (RM)")
            plt.ylabel("Frequency")

        plt.tight_layout()
        plt.show()

    def plot_profit_loss_breakdown(self, enriched_rows, company):
        """
        Visualize what contributes most to profit or loss.
        @param enriched_rows - analysed simulation results
        @param company - Company object
        @return None
        """
        avg_sales = sum(float(r[3]) for r in enriched_rows) / len(enriched_rows)
        avg_cogs = sum(float(r[4]) for r in enriched_rows) / len(enriched_rows)
        avg_marketing = sum(float(r[6]) for r in enriched_rows) / len(enriched_rows)

        fixed_costs = (
            company.rent
            + company.staff_cost
            + company.utilities
            + company.subscriptions
            + company.loan_payment
            + company.other_fixed
        )

        labels = [
            "COGS",
            "Rent",
            "Staff",
            "Other Fixed",
            "Marketing",
        ]

        values = [
            avg_cogs,
            company.rent,
            company.staff_cost,
            fixed_costs - company.rent - company.staff_cost,
            avg_marketing,
        ]

        plt.figure()
        plt.bar(labels, values)
        plt.title("What Drives Profit / Loss (Avg Monthly)")
        plt.ylabel("RM per Month")
        plt.xlabel("Cost Components")
        plt.xticks(rotation=15)
        plt.tight_layout()
        plt.show()

    def plot_overview_dashboard(
        self,
        results,
        company,
        cash_warning_threshold=5000,
        cash_critical_threshold=2000,
    ):

        if not results:
            print("No data available for overview dashboard.")
            return

        num_months = len(results)
        if num_months < 12:
            print(f"\n⚠ Note: Displaying {num_months} month(s) of data (partial year)")
        else:
            print(f"\n✓ Displaying full year ({num_months} months)")

        results = sorted(results, key=lambda r: int(r[2]))

        months = [int(r[2]) for r in results]
        profit = [float(r[7]) for r in results]
        cash = [float(r[8]) for r in results]
        total_profit = sum(profit)
        final_cash = cash[-1]
        avg_profit = float(np.mean(profit))
        max_profit = max(profit)
        min_cash = min(cash)
        best_profit_idx = profit.index(max_profit)
        lowest_cash_idx = cash.index(min_cash)
        month_labels = [calendar.month_abbr[m] for m in months]

        fig, ax1 = plt.subplots(figsize=(13, 8))
        fig.suptitle(
            f"Business Overview – {company.business_id} ({company.business_type.title()}) – {num_months} Month(s)",
            fontsize=18,
            fontweight="bold",
            y=0.96,
        )

        bar_colors = ["#2ecc71" if p >= 0 else "#e74c3c" for p in profit]
        bar_width = 0.6 if num_months >= 6 else 0.4

        ax1.bar(
            months,
            profit,
            width=bar_width,
            color=bar_colors,
            edgecolor="black",
            linewidth=1.5,
            zorder=2,
        )
        ax1.axhline(0, color="black", linewidth=2, alpha=0.8, zorder=3)
        ax1.set_xlabel("Month", fontsize=12, fontweight="bold")
        ax1.set_ylabel("Monthly Profit / Loss (RM)", fontsize=12, fontweight="bold")
        ax1.set_xticks(months)
        ax1.set_xticklabels(month_labels)
        ax1.set_xlim(min(months) - 0.5, max(months) + 0.5)
        ax1.grid(True, axis="y", linestyle="--", alpha=0.4, zorder=1)

        cumulative_profit = np.cumsum(profit)
        ax1.plot(
            months,
            cumulative_profit,
            color="orange",
            linestyle="--",
            linewidth=2,
            marker="o",
            label="Cumulative Profit",
            zorder=4,
        )

        ax2 = ax1.twinx()
        ax2.set_ylabel(
            "Cash Balance (RM) – End of Month",
            color="#2980b9",
            fontsize=12,
            fontweight="bold",
        )
        ax2.tick_params(axis="y", labelcolor="#2980b9")

        for i in range(len(cash) - 1):
            seg_color = "#27ae60" if cash[i + 1] >= cash[i] else "#c0392b"
            ax2.plot(
                months[i : i + 2],
                cash[i : i + 2],
                color=seg_color,
                linewidth=3,
                marker="o",
                zorder=5,
            )

        max_cash = max(cash) if cash else 1.0
        for i, c in enumerate(cash):
            if c < cash_warning_threshold:
                ax2.add_patch(
                    Rectangle(
                        (months[i] - 0.5, 0),
                        width=1,
                        height=max_cash * 1.5,
                        color="red",
                        alpha=0.07,
                        zorder=0,
                    )
                )

        cash_colors = []
        for c in cash:
            if c < cash_critical_threshold:
                cash_colors.append("red")
            elif c < cash_warning_threshold:
                cash_colors.append("yellow")
            else:
                cash_colors.append("green")

        ax2.scatter(
            months,
            cash,
            s=70,
            c=cash_colors,
            edgecolors="black",
            zorder=6,
        )

        for i, c in enumerate(cash):
            dy = 8 if i % 2 == 0 else 20
            ax2.annotate(
                f"RM{c:,.0f}",
                xy=(months[i], c),
                xytext=(0, dy),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
                color="#34495e",
                bbox=dict(facecolor="white", alpha=0.6, edgecolor="none", pad=1.5),
                zorder=7,
            )

        y_span = max(profit) - min(profit) if profit else 1.0
        profit_offset = max(300, 0.10 * y_span)

        best_label = (
            "★ Best Month" if profit[best_profit_idx] > 0 else "★ Least Loss Month"
        )
        ax1.annotate(
            best_label,
            xy=(months[best_profit_idx], profit[best_profit_idx]),
            xytext=(0, 18),
            textcoords="offset points",
            arrowprops=dict(arrowstyle="->", color="green", lw=2, shrinkA=0, shrinkB=6),
            ha="center",
            fontsize=11,
            fontweight="bold",
            color="green",
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=4),
            zorder=8,
        )

        ax2.annotate(
            "Lowest Cash",
            xy=(months[lowest_cash_idx], cash[lowest_cash_idx]),
            xytext=(0, 20),
            textcoords="offset points",
            arrowprops=dict(arrowstyle="->", color="red", lw=2, shrinkA=0, shrinkB=6),
            ha="center",
            fontsize=11,
            fontweight="bold",
            color="darkred",
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=4),
            zorder=8,
        )

        summary_text = (
            f"Months: {num_months}\n"
            f"Total Profit: RM{total_profit:,.0f}\n"
            f"Average Profit: RM{avg_profit:,.0f}\n"
            f"Highest Profit: RM{max_profit:,.0f}\n"
            f"Final Cash: RM{final_cash:,.0f}\n"
            f"Lowest Cash: RM{min_cash:,.0f}"
        )
        fig.text(
            0.97,
            0.97,
            summary_text,
            ha="right",
            va="top",
            fontsize=12,
            bbox=dict(
                facecolor="#ecf0f1",
                edgecolor="#7f8c8d",
                boxstyle="round,pad=0.5",
                alpha=0.95,
            ),
        )

        legend_elements = [
            Patch(facecolor="#2ecc71", label="Profit"),
            Patch(facecolor="#e74c3c", label="Loss"),
            Line2D(
                [0],
                [0],
                color="orange",
                lw=2,
                linestyle="--",
                marker="o",
                label="Cumulative Profit",
            ),
            Line2D([0], [0], color="#27ae60", lw=3, label="Cash Rising"),
            Line2D([0], [0], color="#c0392b", lw=3, label="Cash Falling"),
            Patch(
                facecolor="red",
                alpha=0.07,
                label=f"Cash < RM{cash_warning_threshold} (Risk zone)",
            ),
        ]
        ax1.legend(
            handles=legend_elements,
            loc="upper left",
            bbox_to_anchor=(1.02, 1),
            frameon=True,
            fontsize=9,
        )

        fig.text(
            0.01,
            0.02,
            f"{company.business_id} – Strategy Simulator",
            fontsize=9,
            color="gray",
            alpha=0.6,
        )

        plt.tight_layout(rect=[0, 0.08, 0.85, 0.94])
        plt.show()
