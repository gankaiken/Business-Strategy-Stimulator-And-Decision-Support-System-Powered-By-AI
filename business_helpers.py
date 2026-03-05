"""
Business helper functions for data conversion and editing
"""

from company import Company
from decision import Decision
from input_helper import get_float_or_prompt, get_int_or_prompt
from data_io import (
    save_company,
    save_decision,
    load_decisions,
    set_goal,
    load_history,
    get_goal,
    load_results,
)
import os
import csv
import math


def company_row_to_object(row):
    """
    Convert a CSV row to a Company object with validation.
    @param row - list representing company CSV row
    @return Company object
    """
    values = [
        get_float_or_prompt(v, f"Invalid value at column {i}")
        for i, v in enumerate(row[2:], start=2)
    ]
    row[2:] = map(str, values)
    save_company(row)
    return Company(row[0], row[1], *values)


def decision_rows_to_objects(rows, year, allow_save=False):
    """
    Convert CSV rows to Decision objects with validation.

    @param rows - list of decision CSV rows
    @param year - simulation year
    @return list of Decision objects
    """
    decisions = []

    for r in rows:
        if len(r) == 8:
            r = r + ["HUMAN"]

        business_id = r[0]
        month = get_int_or_prompt(r[2], "Invalid month")

        values = [
            get_float_or_prompt(r[i], f"Invalid value at column {i}")
            for i in range(3, 8)
        ]

        if allow_save:
            save_decision(r, year)
        decisions.append(
            Decision(
                business_id=business_id,
                year=year,
                month=month,
                price_change_pct=values[0],
                marketing_spend=values[1],
                staff_cost_adjustment=values[2],
                waste_reduction_pct=values[3],
                inventory_tightness=values[4],
            )
        )

    return decisions


def edit_decisions(business_id, year):
    """
    Interactive decision editor.
    Allows users to modify monthly decisions.

    @param business_id - business identifier
    @param year - simulation year
    @return None
    """
    decisions = load_decisions(business_id, year, "HUMAN")

    if not decisions:
        print("No decisions found.")
        return

    print("\n===== Edit Monthly Decisions =====")
    for i, d in enumerate(decisions, start=1):
        print(f"{i}. Month {d[2]} | Price {d[3]} | Marketing RM{d[4]}")

    try:
        idx = int(input("\nSelect month to edit (number): ")) - 1
        row = decisions[idx]
    except:
        print("Invalid selection.")
        return

    print("\nEditing Month", row[2])
    print("Press Enter to keep existing value.\n")

    row[3] = prompt_edit("Price change (%)", row[3])
    row[4] = prompt_edit("Marketing spend (RM)", row[4])
    row[5] = prompt_edit("Staff cost adjustment (RM)", row[5])
    row[6] = prompt_edit("Waste reduction (%)", row[6])
    row[7] = prompt_edit("Inventory tightness (0–1)", row[7])

    save_decision(row, year)
    print("\n✔ Decision updated successfully.")


def prompt_edit(label, current):
    """
    Prompt user to edit a value or keep current.

    @param label - description of the field
    @param current - current value
    @return new value or current if user presses Enter
    """
    val = input(f"{label} [current: {current}]: ").strip()
    return val if val else current


def set_goal_interactive(business_id, year):
    """
    Features:
    - Show recent months' cash and profit/loss
    - Calculate actual runway
    - Set a runway goal
    - Optional 'what-if' scenario simulation
    - Display progress bar
    """

    print("\n===== Set Survival Goal =====")
    print(
        " Cash runway = how many months your business can survive if it continues making losses.\n"
    )
    print("Example:")
    print(" Losing RM5,000/month and having RM30,000 → runway = 6 months\n")

    results = load_results(business_id, year)
    if not results:
        print(
            "⚠ No simulation results found yet. Run Option 1 first (Full Business Analysis)."
        )
        input("\nPress Enter to return to menu...")
        return

    profits = [float(r[7]) for r in results]
    cash_ends = [float(r[8]) for r in results]

    print("\nRecent monthly performance:")
    print("Month | Cash End   | Profit/Loss")
    for idx, r in enumerate(results, start=1):
        print(f"{idx:5d} | {float(r[8]):9.2f} | {float(r[7]):11.2f}")

    loss_months = [abs(p) for p in profits if p < 0]
    cash_now = cash_ends[-1]

    if not loss_months:
        actual_runway = math.inf
    else:
        recent_losses = loss_months[-3:] if len(loss_months) >= 3 else loss_months
        avg_loss = sum(recent_losses) / len(recent_losses)
        actual_runway = cash_now / avg_loss if avg_loss > 0 else math.inf

    while True:
        try:
            goal = float(input("\nEnter your runway goal (months): ").strip())
            if goal <= 0:
                print("Runway goal must be positive.")
                continue
            break
        except ValueError:
            print("Invalid input. Enter a number like 6 or 12.")

    print(f"\n✓ Runway goal set to {goal:.1f} months.")

    # Display runway
    def runway_display(x):
        if x == math.inf:
            return "Unlimited"
        if x >= 24:
            return "24+"
        return f"{x:.1f}"

    def runway_bar(actual, goal):
        max_len = 20
        ratio = min(actual / goal, 1) if goal > 0 else 0
        filled = int(max_len * ratio)
        bar = "█" * filled + "-" * (max_len - filled)
        return f"|{bar}| {actual:.1f}/{goal:.1f} months"

    print("\n===== Runway Goal Check =====")
    print(f"Target runway : {goal:.1f} months")
    print(f"Actual runway : {runway_display(actual_runway)} months")
    print(runway_bar(actual_runway, goal))

    # ----------------- Status + Tips -----------------
    ratio = actual_runway / goal if goal > 0 else 0
    if actual_runway == math.inf or ratio >= 1:
        print("SAFE — You have a strong cash buffer!")
        print("Tip: Consider growth or marketing tests.")
    elif ratio >= 0.5:
        short = goal - actual_runway
        print(f"AT RISK — Short by ~{short:.1f} months.")
        print("Tip: Focus on improving sales or reducing losses.")
    else:
        short = goal - actual_runway
        print(f"DANGER — Short by ~{short:.1f} months.")
        print("Tip: Cut costs and boost cash flow urgently.")

    # ----------------- Optional simulation -----------------
    print("\n===== Current Baseline =====")
    print(f"Current available cash : RM{cash_now:,.0f}")

    if actual_runway == math.inf:
        print("Current monthly loss  : None (business not losing money)")
    else:
        print(f"Estimated monthly loss: RM{avg_loss:,.0f}")
        print(f"Estimated runway      : {actual_runway:.1f} months")

    print("\nNow imagine a future scenario.")
    print("For example:")
    print("- You plan to cut costs")
    print("- You expect higher sales")
    print("- You will inject more cash")
    print("\nEnter what you EXPECT after those changes.\n")

    simulate = (
        input("Want to simulate changes in cash or losses? (y/n): ").strip().lower()
    )

    if simulate == "y":
        while True:
            try:
                new_cash = float(
                    input("Enter expected available cash (RM) after changes: ")
                )
                if new_cash < 0:
                    print("⚠ Cash cannot be negative. Try again.")
                    continue
                new_loss = float(
                    input("Enter expected MONTHLY loss (RM, positive number): ")
                )
                if new_loss <= 0:
                    print("⚠ Monthly loss must be greater than 0.")
                    continue
                if new_loss < 100:
                    print("⚠ Monthly loss seems very small. Please double-check.")
                    confirm = input("Proceed anyway? (y/n): ").strip().lower()
                    if confirm != "y":
                        continue
                break

            except ValueError:
                print("⚠ Invalid input. Please enter numbers only.")

    projected_runway = new_cash / new_loss if new_loss > 0 else math.inf

    print("\n===== Your What-If Scenario =====")
    print(f"Projected cash   : RM{new_cash:,.0f}")
    print(f"Projected loss   : RM{new_loss:,.0f} / month")
    print(f"Projected runway : {runway_display(projected_runway)} months")
    print(runway_bar(projected_runway, goal))

    input("\nPress Enter to return to menu...")


def load_latest_results(business_id):
    """
    Load the most recent simulation results for a business.
    Returns enriched rows or None if not found.
    """

    RESULTS_DIR = "results"  # change if your folder name differs

    if not os.path.exists(RESULTS_DIR):
        return None

    # Find all result files for this business
    matching_files = [
        f
        for f in os.listdir(RESULTS_DIR)
        if f.startswith(f"results_{business_id}_") and f.endswith(".csv")
    ]

    if not matching_files:
        return None

    # Sort by filename (year is usually embedded → latest last)
    matching_files.sort(reverse=True)
    latest_file = matching_files[0]

    filepath = os.path.join(RESULTS_DIR, latest_file)

    results = []

    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)  # skip header if present

            for row in reader:
                if not row or len(row) < 9:
                    continue  # skip malformed rows
                results.append(row)

    except Exception as e:
        print(f"ERROR loading results: {e}")
        return None

    return results if results else None


def review_past_scenarios(business_id):
    """
    Option 4:
    Review and compare past simulation runs.
    """

    history = load_history(business_id)

    if not history:
        print("\n⚠ No past simulation runs found.")
        print("Run Option 1 (Full Business Analysis) first.")
        input("\nPress Enter to return to menu...")
        return

    print("\n===== Past Simulation Comparison =====")

    # Sort newest first
    history = sorted(
        history,
        key=lambda h: h.get("run_datetime", ""),
        reverse=True,
    )

    best_profit = None
    worst_profit = None

    for idx, h in enumerate(history, start=1):
        try:
            total_profit = float(h["total_profit"])
            ending_cash = float(h["ending_cash"])
            min_runway = float(h["min_runway"])
        except:
            continue

        risk = "Low" if min_runway >= 6 else "Moderate" if min_runway >= 3 else "High"

        print(f"\nScenario {idx}")
        print(f"Date        : {h['date']}")
        print(f"Total Profit: RM{total_profit:,.0f}")
        print(f"Final Cash  : RM{ending_cash:,.0f}")
        print(f"Min Runway  : {min_runway:.1f} months")
        print(f"Health      : {h['health_mostly']}")
        print(f"Risk Level  : {risk}")

        if best_profit is None or total_profit > best_profit["profit"]:
            best_profit = {"profit": total_profit, "idx": idx}

        if worst_profit is None or total_profit < worst_profit["profit"]:
            worst_profit = {"profit": total_profit, "idx": idx}

    print("\n===== Summary Insights =====")
    print(f"Best run  : Scenario {best_profit['idx']} (RM{best_profit['profit']:,.0f})")
    print(
        f"Worst run: Scenario {worst_profit['idx']} (RM{worst_profit['profit']:,.0f})"
    )
    print("💡 Tip: Compare decisions that led to better runway and profit.")

    input("\nPress Enter to return to menu...")
