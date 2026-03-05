"""
This module contains the main simulation execution logic including:
- Full year simulation
- Quick health checks
- Sensitivity testing
- Scenario management
"""

from datetime import datetime
from data_io import (
    load_company,
    load_decisions,
    save_results,
    load_results,
    save_history,
)
from business_helpers import company_row_to_object, decision_rows_to_objects
from market import create_default_market
from simulation import BusinessSimulator
from analysis import SMEAdvisor, explain_root_cause
from visualization import Visualizer
from scenario_manager import load_scenarios
from sensitivity import run_sensitivity
from report_generator import (
    numeric_recommendations_text,
    print_vision_board,
    print_numeric_recommendations,
    print_cash_histogram,
    show_cause_weights,
    compare_before_after,
    compare_risk,
    check_milestones,
    vision_board_text,
)
import matplotlib.pyplot as plt
from data_io import save_decision
from optimizer import GeneticOptimizer


class Logger:
    def __init__(self, callback=None):
        self.callback = callback
        self.lines = []

    def log(self, msg=""):
        msg = str(msg)
        self.lines.append(msg)
        if self.callback:
            self.callback(msg)

    def text(self):
        return "\n".join(self.lines)


def quick_check_in(business_id, year):
    """
    Quick health check showing last recorded results.

    @param business_id - business identifier
    @param year - simulation year
    @return None
    """
    results = load_results(business_id, year)
    if not results:
        print("No previous results found.")
        return

    last = results[-1]
    print("\n===== Quick Health Check =====")
    print("Last recorded month:")
    print(f"• Profit/Loss : RM{float(last[7]):,.0f}")
    print(f"• Cash Runway : {last[10]} months")
    print(f"• Health      : {last[11]}")

    if last[11] == "RED":
        print("\n⚠ Action recommended: Run full business analysis")
    elif last[11] == "YELLOW":
        print("\n⚠ Action recommended: Monitor closely or test improvements")
    else:
        print("\n✓ Business appears stable")


def scenario_menu(business_id, year):
    """
    Display saved scenarios for comparison.

    @param business_id - business identifier
    @param year - simulation year
    @return None
    """
    scenarios = load_scenarios(business_id, year)

    if not scenarios:
        print("\n⚠ No scenarios saved yet.")
        print("Run a simulation and save a scenario first.")
        return

    print("\n===== Scenario Comparison =====")

    for i, s in enumerate(scenarios, start=1):
        print(f"\nScenario {i}: {s['scenario_name']}")
        print(f"Date        : {s['created_at']}")
        print(f"Profit      : RM{float(s['total_profit']):,.0f}")
        print(f"Final Cash  : RM{float(s['ending_cash']):,.0f}")
        print(f"Min Runway  : {s['min_runway']}")
        print(f"Health      : {s['health_mostly']}")
        print(f"Readiness   : {s['readiness']}")
        print(f"Root Cause  : {s['root_cause']}")

    input("\nPress Enter to return to menu...")


def interactive_recommendation_impact(enriched_rows):
    """
    Allow user to accept or adjust recommendation impact
    """
    avg_profit = sum(float(r[7]) for r in enriched_rows) / len(enriched_rows)

    while True:
        print("\nDo you agree with the recommended improvements?")
        print("1. Yes (use suggested 40% improvement)")
        print("2. No (I want to choose my own improvement level)")

        choice = input("Choice (1 or 2): ").strip()

        if choice in ("1", "2"):
            break
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

    improvement_pct = 40

    if choice == "2":
        print("\nWhat does this mean?")
        print("- 20%  = small improvement")
        print("- 40%  = strong improvement (recommended)")
        print("- 60%+ = aggressive turnaround")
        print("\nExample:")
        print("If current loss is RM10,000:")
        print("• 20% → RM8,000 loss")
        print("• 40% → RM6,000 loss")
        print("• 60% → RM4,000 loss")

        while True:
            try:
                pct = float(input("\nEnter improvement percentage (0–100): "))
                if 0 <= pct <= 100:
                    improvement_pct = pct
                    break
                else:
                    print("⚠ Please enter a number between 0 and 100.")
            except ValueError:
                print("⚠ Invalid input. Please enter a number.")

    improvement_factor = 1 - (improvement_pct / 100)
    projected_profit = avg_profit * improvement_factor

    print("\n===== Recommendation Impact =====")
    print(f"Current average monthly outcome : RM{avg_profit:,.0f}")
    print(f"Chosen improvement level        : {improvement_pct:.0f}%")
    print(f"Projected monthly outcome       : RM{projected_profit:,.0f}")

    if projected_profit >= 0:
        print("✅ Business turns profitable under this scenario.")
    else:
        print("⚠ Business still loss-making, but risk is reduced.")

    return avg_profit, projected_profit


def run_simulation_for_year(business_id, year):
    """
    Run yearly simulation, analysis, recommendations, and Monte Carlo risk assessment.
    """
    print("\n===== Full Business Analysis =====")
    print("This analysis will help you answer three key questions:")
    print("1. Is my business making money?")
    print("2. If not, why?")
    print("3. What should I focus on next?")
    print("")
    print("The system will simulate 12 months, analyse performance,")
    print("and give practical recommendations.")
    input("\nPress Enter to start analysis...")

    # Load company and decisions
    company_row = load_company(business_id)
    if not company_row:
        print("Company not found.")
        return

    company = company_row_to_object(company_row)

    decision_rows = load_decisions(business_id, year, source="HUMAN")
    if not decision_rows:
        print("No decisions found for this year.")
        return

    decisions = decision_rows_to_objects(decision_rows, year, allow_save=True)

    # Core objects
    market = create_default_market(company.business_type)
    simulator = BusinessSimulator(seed=42)
    advisor = SMEAdvisor()
    viz = Visualizer()

    # Baseline simulation
    results = simulator.simulate_12_months(company, market, decisions)
    enriched = advisor.analyse_year(company, results)
    save_results(enriched, year)

    # Month-by-month analysis
    print("Below is a month-by-month explanation of your business performance.\n")
    for r in enriched:
        profit = float(r[7])
        print(
            f"Month {r[2]} | "
            f"{'Profit' if profit >= 0 else 'Loss'} RM{abs(profit):,.0f} | "
            f"Runway {r[10]} | Health {r[11]}"
        )
        print("Summary:", r[16])
        print("Root Cause:", explain_root_cause(r[15]))
        print("Readiness:", r[17])
        print("-" * 40)

    check_milestones(enriched)
    print("\n" + "=" * 60)
    print("VISUAL OVERVIEW - YEAR AT A GLANCE")
    print("=" * 60)
    print("\nShowing dashboard overview...")
    input("Press Enter to view dashboard...")

    viz.plot_overview_dashboard(enriched, company)

    input("\nPress Enter to continue to detailed analysis...")

    # Sensibility and recommendations
    print_vision_board(enriched, company)
    print_numeric_recommendations(enriched, company)
    print("\n===== What Actually Matters Most (Sensitivity Test) =====")
    test_month = int(enriched[-1][2])
    base_decision = next(d for d in decisions if d.month == test_month)
    cash_start = company.starting_cash
    for r in enriched:
        if int(r[2]) < test_month:
            cash_start = float(r[8])

    sensitivity_results = run_sensitivity(
        month=test_month,
        base_decision=base_decision,
        company=company,
        market=market,
        simulator=simulator,
        cash_start=cash_start,
    )

    for idx, r in enumerate(sensitivity_results, start=1):
        arrow = "↑" if r["profit_change"] > 0 else "↓"
        print(f"{idx}. {r['lever']:<22} {arrow} RM{abs(r['profit_change']):,.0f}/month")

    if sensitivity_results:
        best = sensitivity_results[0]
        print(f"\n✅ Focus first on: {best['lever']}")

    # Recommendation impact
    avg_profit, projected_profit = interactive_recommendation_impact(enriched)

    # Monte Carlo risk analysis
    print("\nRunning Monte Carlo risk analysis (current strategy)...")
    all_mc, stats = simulator.monte_carlo_full_year(
        company, market, decisions, business_id, year, num_runs=500
    )

    before_metrics = {
        "avg_profit": avg_profit,
        "final_cash": float(enriched[-1][8]),
        "bankruptcy_prob": stats["bankruptcy_prob"],
    }

    risk_level = (
        "Low"
        if stats["bankruptcy_prob"] < 10
        else "Moderate" if stats["bankruptcy_prob"] < 30 else "High"
    )

    print(
        f"\nRisk Level: {risk_level} "
        f"({stats['bankruptcy_prob']:.1f}% chance of running out of cash)"
    )

    # Improvements if high risk
    if stats["bankruptcy_prob"] >= 30:
        print("\n⚠ Business is still at HIGH RISK.")

        top_problem = show_cause_weights(enriched)
        print("\nMain problem detected:", top_problem)

        print("\nWhat would you like to improve next?")
        print("1. Increase sales")
        print("2. Reduce staff cost")
        print("3. Improve margin")
        print("4. Skip improvements")

        choice = input("Choice: ").strip()

        original_sales = company.baseline_sales
        original_staff = company.staff_cost
        original_cogs = company.baseline_cogs

        try:
            if choice == "1":
                pct = float(input("Increase sales by % (e.g. 10): "))
                company.baseline_sales *= 1 + pct / 100

            elif choice == "2":
                pct = float(input("Reduce staff cost by % (e.g. 10): "))
                company.staff_cost *= 1 - pct / 100

            elif choice == "3":
                pct = float(input("Improve margin by % (e.g. 5): "))
                company.baseline_cogs *= 1 - pct / 100

            else:
                print("No changes applied.")

        except ValueError:
            print("Invalid input. No changes applied.")

        if choice in ["1", "2", "3"]:
            new_results = simulator.simulate_12_months(company, market, decisions)
            new_enriched = advisor.analyse_year(company, new_results)

            _, new_stats = simulator.monte_carlo_full_year(
                company, market, decisions, business_id, year, num_runs=300
            )

            after_metrics = {
                "avg_profit": sum(float(r[7]) for r in new_enriched)
                / len(new_enriched),
                "final_cash": float(new_enriched[-1][8]),
                "bankruptcy_prob": new_stats["bankruptcy_prob"],
            }

            compare_before_after(before_metrics, after_metrics)
            compare_risk(stats, new_stats)

        # Restore original company values
        company.baseline_sales = original_sales
        company.staff_cost = original_staff
        company.baseline_cogs = original_cogs

    # Visualizations
    while True:
        print("\nWould you like to view visual charts?")
        print("1. Yes (step-by-step)")
        print("2. Skip charts")
        choice = input("Choice (1 or 2): ").strip()

        if choice in ("1", "2"):
            break
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

    if choice == "1":
        charts = [
            (
                "YEAR OVERVIEW DASHBOARD",
                lambda: viz.plot_overview_dashboard(enriched, company),
            ),
            ("CASH FLOW OVER TIME", lambda: viz.plot_cash_over_time(enriched)),
            ("PROFIT & LOSS TREND", lambda: viz.plot_profit_over_time(enriched)),
            ("SALES TREND", lambda: viz.plot_sales_over_time(enriched)),
            ("COST BREAKDOWN", lambda: viz.plot_cost_breakdown(enriched, company)),
        ]

        for idx, (title, plot_func) in enumerate(charts, start=1):
            print(f"\n=== {title} ({idx}/{len(charts)}) ===")
            plot_func()

            if idx < len(charts):
                if input("Press Enter for next chart or 'q' to quit: ").lower() == "q":
                    break

    # Monte Carlo histogram
    ending_cash_list = [r["ending_cash"] for r in all_mc]
    print_cash_histogram(ending_cash_list)

    # Save history
    runways = [float(r[10]) for r in enriched if r[10] != "Not Losing Money"]
    min_runway = min(runways) if runways else "Stable"
    save_history(
        business_id,
        {
            "date": datetime.now().date().isoformat(),
            "run_datetime": datetime.now().isoformat(),
            "decision_source": "HUMAN",
            "total_profit": sum(float(r[7]) for r in enriched),
            "ending_cash": enriched[-1][8],
            "min_runway": min_runway,
            "health_mostly": enriched[-1][11],
            "notes": "",
        },
    )

    print("\n===== Analysis Summary =====")

    final_profit = sum(float(r[7]) for r in enriched)
    final_cash = float(enriched[-1][8])
    final_health = enriched[-1][11]

    print(f"Total yearly outcome : RM{final_profit:,.0f}")
    print(f"Ending cash balance  : RM{final_cash:,.0f}")
    print(f"Overall health       : {final_health}")

    if final_health == "GREEN":
        print("✅ Business is financially stable.")
        print("💡 Focus on growth, efficiency, or expansion planning.")
    elif final_health == "YELLOW":
        print("⚠️ Business is under pressure.")
        print("💡 Improve margins or sales before expanding.")
    else:
        print("🚨 Business is at high financial risk.")
        print("💡 Immediate action needed: cut costs or boost revenue.")

    print("\n✓ Full business analysis complete.")
    print("Next step → Review scenarios, test sensitivity, or adjust decisions.")
    input("\nPress Enter to return to menu...")


def run_sensitivity_test(business_id, year):
    """
    Menu-level sensitivity analysis.
    Tests which lever has the biggest impact on profit.
    """

    print("\n===== Sensitivity Analysis =====")
    print("What is sensitivity analysis?")
    print("→ It shows which business decision affects profit the MOST")
    print("  when changed slightly.")
    print("")
    print("This helps you focus on what actually matters,")
    print("instead of changing everything at once.")
    print("")
    print("The system will test small changes to:")
    print("- Pricing")
    print("- Marketing spend")
    print("- Staff cost")
    print("- Waste reduction")

    input("\nPress Enter to run sensitivity test...")

    # Load company and decisions
    company_row = load_company(business_id)
    if not company_row:
        print("Company not found.")
        return
    company = company_row_to_object(company_row)
    decision_rows = load_decisions(business_id, year, source="HUMAN")
    if not decision_rows:
        print("No decisions found.")
        return

    decisions = decision_rows_to_objects(decision_rows, year, allow_save=True)

    # Baseline month
    base_decision = decisions[0]
    print("\nNote:")
    print("This test uses one representative month")
    print("to isolate the impact of each decision clearly.")
    month = base_decision.month

    market = create_default_market(company.business_type)
    simulator = BusinessSimulator(seed=42)
    cash_start = company.starting_cash
    sensitivity_results = run_sensitivity(
        month=month,
        base_decision=base_decision,
        company=company,
        market=market,
        simulator=simulator,
        cash_start=cash_start,
    )

    print("\n===== Sensitivity Results =====")
    print("Impact on monthly profit when each lever is adjusted slightly:\n")

    for result in sensitivity_results:
        lever = result["lever"]
        impact = result["profit_change"]
        direction = "↑" if impact > 0 else "↓"
        print(f"{lever:<25}: {direction} RM{abs(impact):,.0f}")

    if sensitivity_results:
        biggest = sensitivity_results[0]["lever"]

        print("\n===== Sensitivity Insight =====")
        print(f" Most impactful lever: {biggest}")
        print(
            "This lever causes the largest change in profit\n"
            "even with a small adjustment."
        )

        print("\n How to use this insight:")
        print(
            f"- Focus on improving **{biggest}** first\n"
            "- Small changes here give the biggest payoff\n"
            "- Avoid spreading effort across low-impact areas"
        )
    else:
        print("\n No sensitivity data available.")

    input("\nPress Enter to return to menu...")


def run_full_analysis_workflow_gui(
    business_id,
    year,
    decision_source="HUMAN",
    num_mc_runs=500,
    progress_callback=None,
    log_callback=None,
):
    logger = Logger(callback=log_callback)

    company_row = load_company(business_id)
    if not company_row:
        raise ValueError("Company not found")
    company = company_row_to_object(company_row)

    decision_rows = load_decisions(business_id, year, source=decision_source)
    if not decision_rows:
        raise ValueError("No decisions found")
    decisions = decision_rows_to_objects(decision_rows, year, allow_save=False)

    market = create_default_market(company.business_type)
    simulator = BusinessSimulator(seed=42)
    advisor = SMEAdvisor()
    viz = Visualizer()

    logger.log("===== Full Business Analysis =====")
    logger.log("Running 12-month simulation...")

    results = simulator.simulate_12_months(company, market, decisions)
    enriched = advisor.analyse_year(company, results)
    save_results(enriched, year)
    logger.log("")
    logger.log("===== Month-by-Month Performance =====")
    logger.log("")

    for r in enriched:
        profit = float(r[7])
        logger.log(
            f"Month {r[2]} | "
            f"{'Profit' if profit >= 0 else 'Loss'} RM{abs(profit):,.0f} | "
            f"Runway {r[10]} | Health {r[11]}"
        )
        logger.log(f"Summary: {r[16]}")
        logger.log(f"Root Cause: {explain_root_cause(r[15])}")
        logger.log(f"Readiness: {r[17]}")
        logger.log("-" * 40)

    # milestone
    for row in enriched:
        month = int(row[2])
        profit = float(row[7])
        runway = row[10]
        if profit > 0:
            logger.log(f"🎉 Milestone: First profitable month at Month {month}")
            break
        if runway != "Not Losing Money" and float(runway) < 3:
            logger.log("⚠ Warning: Cash runway below 3 months")
            break

    # Dashboard and recommendations
    logger.log("")
    logger.log("===== Business Health Dashboard =====")
    logger.log(vision_board_text(enriched, company))

    logger.log("")
    logger.log("===== Recommended Actions =====")
    logger.log(numeric_recommendations_text(enriched, company))

    # Sensitivity test
    logger.log("")
    logger.log("===== What Actually Matters Most (Sensitivity Test) =====")

    test_month = int(enriched[-1][2])
    base_decision = next(d for d in decisions if d.month == test_month)

    cash_start = company.starting_cash
    for r in enriched:
        if int(r[2]) < test_month:
            cash_start = float(r[8])

    sensitivity_results = run_sensitivity(
        month=test_month,
        base_decision=base_decision,
        company=company,
        market=market,
        simulator=simulator,
        cash_start=cash_start,
    )

    for idx, r in enumerate(sensitivity_results, start=1):
        arrow = "↑" if r["profit_change"] > 0 else "↓"
        logger.log(
            f"{idx}. {r['lever']:<22} {arrow} RM{abs(r['profit_change']):,.0f}/month"
        )

    if sensitivity_results:
        best = sensitivity_results[0]
        logger.log(f"✅ Focus first on: {best['lever']}")

    # Monte Carlo risk analysis
    logger.log("")
    logger.log(f"Running Monte Carlo risk analysis ({num_mc_runs} runs)...")

    all_mc, mc_stats = simulator.monte_carlo_full_year(
        company,
        market,
        decisions,
        business_id,
        year,
        num_runs=num_mc_runs,
        verbose=False,
        progress_callback=progress_callback,
    )

    ending_cash_list = [r["ending_cash"] for r in all_mc]

    risk_level = (
        "Low"
        if mc_stats["bankruptcy_prob"] < 10
        else "Moderate" if mc_stats["bankruptcy_prob"] < 30 else "High"
    )
    logger.log(
        f"Risk Level: {risk_level} "
        f"({mc_stats['bankruptcy_prob']:.1f}% chance of running out of cash)"
    )

    # Save history
    last = enriched[-1]

    runway_values = [
        float(r[10]) for r in enriched if r[10] not in ("Not Losing Money", "", None)
    ]
    min_runway = min(runway_values) if runway_values else "Stable"

    run_data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "run_datetime": datetime.now().isoformat(timespec="seconds"),
        "decision_source": decision_source,
        "total_profit": sum(float(r[7]) for r in enriched),
        "ending_cash": float(last[8]),
        "min_runway": min_runway,
        "health_mostly": last[11],
        "notes": "",
    }

    save_history(business_id, run_data)
    return {
        "company": company,
        "enriched": enriched,
        "sensitivity_results": sensitivity_results,
        "mc_stats": mc_stats,
        "ending_cash_list": ending_cash_list,
        "log_text": logger.text(),
        "plotters": {
            "dashboard": lambda: viz.plot_overview_dashboard(enriched, company),
            "cash": lambda: viz.plot_cash_over_time(enriched),
            "profit": lambda: viz.plot_profit_over_time(enriched),
            "sales": lambda: viz.plot_sales_over_time(enriched),
            "cost": lambda: viz.plot_cost_breakdown(enriched, company),
            "mc_hist": lambda: viz.plot_cash_histogram(ending_cash_list),
        },
    }


def run_simulation_for_year_gui(
    business_id,
    year,
    decision_source="HUMAN",
    num_mc_runs=500,
    progress_callback=None,
    log_callback=None,
):
    data = run_full_analysis_workflow_gui(
        business_id,
        year,
        decision_source=decision_source,
        num_mc_runs=num_mc_runs,
        progress_callback=progress_callback,
        log_callback=log_callback,
    )
    return data["enriched"]


def run_intelligent_advisor(business_id, year):
    print("\nIntelligent Advisor is running...")
    print("This may take a few minutes.")
    print(
        "The system will try thousands of strategies, simulate 12 months, and learn which decisions give high profit with low risk.\n"
    )

    company_row = load_company(business_id)
    if not company_row:
        print("Company not found.")
        return

    company = company_row_to_object(company_row)
    market = create_default_market(company.business_type)
    simulator = BusinessSimulator(seed=42)

    print("Fitness score combines:")
    print(" - Total yearly profit (70%)")
    print(" - Worst cash runway month (20%)")
    print(" - Bankruptcy penalty\n")

    input("\nPress ENTER to start the AI learning process...")

    optimizer = GeneticOptimizer()

    best_decisions, best_fitness, ga_logs = optimizer.optimize_with_logs(
        company, market, simulator, business_id, year
    )

    if not ga_logs:
        print("No genetic algorithm logs available.")
        return

    # === Display raw GA logs ===
    print("\n--- Genetic Algorithm Progress ---\n")

    show_logs = input(
        "\nPress ENTER to see full GA progress, or type 'skip' to go straight to summary: "
    )
    if show_logs.strip().lower() != "skip":
        # === Display raw GA logs ===
        print("\n--- Genetic Algorithm Progress ---\n")

        max_fitness = max(f for _, f in ga_logs)
        prev_fitness = ga_logs[0][1]

        for gen, fitness in ga_logs:
            bar_length = 30
            filled_len = int(bar_length * fitness / max_fitness)
            bar = "█" * filled_len + "-" * (bar_length - filled_len)

            color_code = "\033[92m" if fitness >= prev_fitness else "\033[91m"
            print(f"Gen {gen:3}: {color_code}{bar}\033[0m {fitness:,.2f}")

            prev_fitness = fitness
    else:
        print("\nSkipping full GA progress. Showing only summary...\n")

    # === Save AI decisions ===
    for d in best_decisions:
        save_decision(
            [
                str(d.business_id),
                str(d.year),
                str(d.month),
                f"{d.price_change_pct:.6f}",
                f"{d.marketing_spend:.2f}",
                f"{d.staff_cost_adjustment:.2f}",
                f"{d.waste_reduction_pct:.6f}",
                f"{d.inventory_tightness:.6f}",
                "AI",
            ],
            year,
        )

    # === Summary ===
    print("\n=== Intelligent Advisor Summary ===")
    print(f"Final Best Fitness Score: {best_fitness:,.2f}")
    print("Fitness accounts for:")
    print(" - Total yearly profit")
    print(" - Worst cash runway month")
    print(" - Bankruptcy risk penalty")
    print(
        "\nTo see month-by-month profit, run Full Business Analysis using AI decisions.\n"
    )

    print("Key Actions by Month:")
    for d in best_decisions:
        action_summary = (
            f"Month {d.month:2}: "
            f"Price {'increase' if d.price_change_pct > 0 else 'decrease'} {abs(d.price_change_pct*100):.1f}%, "
            f"Marketing spend RM{d.marketing_spend:,.0f}, "
            f"Staff cost {'increase' if d.staff_cost_adjustment > 0 else 'decrease'} RM{abs(d.staff_cost_adjustment):,.0f}, "
            f"Waste reduction {d.waste_reduction_pct*100:.1f}%, "
            f"Inventory level {d.inventory_tightness:.2f}"
        )
        print(action_summary)

    print("\n Genetic Algorithm Summary:")
    print(
        "The AI started with random business strategies and improved them step by step.\n"
    )

    print(f"Total learning rounds (generations): {len(ga_logs)}")
    print("  --> Each round = AI tries many strategies and keeps the best ones\n")

    starting_score = ga_logs[0][1]
    final_score = best_fitness
    improvement = final_score - starting_score

    print(f"Starting performance score: {starting_score:,.2f}")
    print(f"Final performance score: {final_score:,.2f}")
    print(f"Overall improvement: +{improvement:,.2f}")
    print(
        "  --> Higher score means better profit, safer cash flow, and lower bankruptcy risk"
    )

    if final_score < 50_000:
        health_level = "Poor 🚨"
    elif final_score < 100_000:
        health_level = "Stable ⚖️"
    else:
        health_level = "Strong ✅"

    estimated_profit = final_score * 0.8  # example conversion factor

    summary_line = (
        f"AI improved your business strategy from {starting_score:,.0f} → {final_score:,.0f} "
        f"(+{improvement:,.0f}). Business Health: {health_level}. "
        f"Estimated yearly profit: RM{estimated_profit:,.0f}."
    )
    print("\n Executive AI Summary:")
    print(summary_line)
    print("\n------------------------------------------------------------------------")
    print("\n In conclusion:")
    print("The AI learned how your business performs best:")
    print(" - Prices are optimized to drive volume")
    print(" - Waste is aggressively reduced")
    print(" - Staff costs are controlled")
    print(" - Inventory is kept tight to avoid tying up cash")
    print(
        "\nFollowing this plan is expected to improve performance while reducing the risk of cash flow problems."
    )
    input("\nPress ENTER to return to the menu...")
