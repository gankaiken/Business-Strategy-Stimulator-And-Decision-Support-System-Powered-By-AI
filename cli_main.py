"""
Main entry point for the Business Strategy Simulator.

This file contains only the main menu and program initialization.
All business logic has been moved to separate modules for better organization.
"""

import os
from schemas import (
    COMPANY_CSV,
    DECISIONS_CSV_TEMPLATE,
    COMPANY_COLUMNS,
    DECISION_COLUMNS,
)
from data_io import ensure_csv_exists
from simulation_controller import (
    run_simulation_for_year,
    quick_check_in,
    scenario_menu,
    run_sensitivity_test,
    run_intelligent_advisor,
)
from business_helpers import edit_decisions, set_goal_interactive, review_past_scenarios
from user_profiles import select_user, select_business, select_year


def safe_input(prompt: str) -> str:
    """
    Safely read user input.
    Prevents EOFError crashes when stdin is unavailable.
    """
    try:
        return input(prompt).strip()
    except EOFError:
        print("\nInput stream closed. Please run this program in a terminal.")
        raise SystemExit


def main():
    """
    Main entry point for the Business Strategy Simulator.
    Displays menu and routes user choices to appropriate handlers.
    """
    user_id = select_user()
    business_id = select_business(user_id)
    year = select_year(user_id, business_id)

    # Ensure required CSV files exist
    if not os.path.exists(COMPANY_CSV):
        ensure_csv_exists(COMPANY_CSV, COMPANY_COLUMNS)
        print("company.csv created. Please fill it first.")
        return

    decisions_csv = DECISIONS_CSV_TEMPLATE.format(year=year)
    if not os.path.exists(decisions_csv):
        ensure_csv_exists(decisions_csv, DECISION_COLUMNS)
        print(f"{decisions_csv} created. Please fill it first.")
        return

    # Main menu loop
    while True:
        print("\n===== Business Strategy Simulator =====")
        print("What would you like to do?")
        print("0. Quick Health Check (last results)")
        print("1. Run Full Business Analysis (simulate this year)")
        print("2. Edit Monthly Decisions")
        print("3. Set Survival Goal (cash runway target)")
        print("4. Review Past Runs (history comparison)")
        print("5. Sensitivity Test (What matters most?)")
        print("6. Run Intelligent Advisor (Optimize Decisions)")
        print("7. Exit")

        choice = safe_input("Choice: ")

        if choice == "0":
            quick_check_in(business_id, year)
        elif choice == "1":
            run_simulation_for_year(business_id, year)
        elif choice == "2":
            edit_decisions(business_id, year)
        elif choice == "3":
            set_goal_interactive(business_id, year)
        elif choice == "4":
            review_past_scenarios(business_id)
        elif choice == "5":
            run_sensitivity_test(business_id, year)
        elif choice == "6":
            run_intelligent_advisor(business_id, year)
        elif choice == "7":
            print("\nThank you for using Business Strategy Simulator!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
