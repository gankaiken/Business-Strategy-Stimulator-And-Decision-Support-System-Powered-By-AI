"""
A scenario represents one complete strategy (set of decisions) and its overall outcome for comparison with other strategies.
"""

from datetime import datetime
from schemas import (
    SCENARIO_CSV_TEMPLATE,
    SCENARIO_COLUMNS,
)
from data_io import ensure_csv_exists, read_csv, write_csv


def save_scenario(business_id, year, scenario_name, enriched_rows, notes=""):
    """
    Save a scenario summary for later comparison.
    @param business_id - business identifier
    @param year - simulation year
    @param scenario_name - name given by user
    @param enriched_rows - analysed monthly results
    @param notes - optional user notes
    @return None
    """

    file_path = SCENARIO_CSV_TEMPLATE.format(business_id=business_id, year=year)
    ensure_csv_exists(file_path, SCENARIO_COLUMNS)
    total_profit = sum(float(r[7]) for r in enriched_rows)
    ending_cash = float(enriched_rows[-1][8])
    runways = []
    for r in enriched_rows:
        if r[10] != "Not Losing Money":
            runways.append(float(r[10]))
    min_runway = min(runways) if runways else "Stable"

    health_count = {}
    for r in enriched_rows:
        flag = r[11]
        health_count[flag] = health_count.get(flag, 0) + 1
    health_mostly = max(health_count, key=health_count.get)

    # Use last month insight
    last_row = enriched_rows[-1]
    readiness = last_row[17]
    root_cause = last_row[15]

    rows = read_csv(file_path)
    rows.append(
        [
            scenario_name,
            datetime.now().isoformat(),
            f"{total_profit:.2f}",
            f"{ending_cash:.2f}",
            str(min_runway),
            health_mostly,
            readiness,
            root_cause,
            "Draft",  # default status
            notes,
        ]
    )

    write_csv(file_path, SCENARIO_COLUMNS, rows)


def load_scenarios(business_id, year):
    """
    Load all saved scenarios for a business and year.
    @param business_id - business identifier
    @param year - simulation year
    @return list - list of scenario dictionaries
    """
    file_path = SCENARIO_CSV_TEMPLATE.format(business_id=business_id, year=year)

    rows = read_csv(file_path)
    scenarios = []

    for r in rows:
        scenarios.append(dict(zip(SCENARIO_COLUMNS, r)))

    return scenarios


def update_scenario_status(business_id, year, scenario_name, new_status):
    """
    Update the status of a saved scenario.
    @param business_id - business identifier
    @param year - simulation year
    @param scenario_name - scenario to update
    @param new_status - Draft / Approved / Rejected
    @return bool - True if updated, False otherwise
    """
    file_path = SCENARIO_CSV_TEMPLATE.format(business_id=business_id, year=year)

    rows = read_csv(file_path)
    if not rows:
        return False

    # Update the most recent matching scenario
    for i in range(len(rows) - 1, -1, -1):
        if rows[i][0] == scenario_name:
            rows[i][8] = new_status
            write_csv(file_path, SCENARIO_COLUMNS, rows)
            return True

    return False
