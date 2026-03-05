"""
This file handles reading and writing CSV files for the
Business Strategy Simulator and Decision Support System.
"""

import csv
import os
from schemas import (
    COMPANY_CSV,
    DECISIONS_CSV_TEMPLATE,
    RESULTS_CSV_TEMPLATE,
    COMPANY_COLUMNS,
    DECISION_COLUMNS,
    RESULT_COLUMNS,
    HISTORY_COLUMNS,
    HISTORY_CSV_TEMPLATE,
)

_runway_goal = None


def set_runway_goal(months):
    global _runway_goal
    _runway_goal = float(months)


def get_runway_goal():
    return _runway_goal


def ensure_csv_exists(file_path, columns):
    """
    Create a CSV file with header row if it does not exist.
    If file exists but header is outdated, migrate rows safely.
    """
    folder = os.path.dirname(file_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(",".join(columns) + "\n")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(",".join(columns) + "\n")
        return

    existing_header = lines[0].strip().split(",")

    if existing_header == columns:
        return

    old_rows = [line.strip().split(",") for line in lines[1:]]
    new_rows = []

    for row in old_rows:
        padded = row[:]
        while len(padded) < len(columns):
            padded.append("HUMAN")
        new_rows.append(padded[: len(columns)])

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(",".join(columns) + "\n")
        for r in new_rows:
            f.write(",".join(r) + "\n")


def read_csv(file_path):
    """
    Read a CSV file and return rows (excluding header).
    """
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    rows = []
    for line in lines[1:]:
        rows.append(line.strip().split(","))

    return rows


def write_csv(file_path, columns, rows):
    """
    Write rows to a CSV file (overwrite).
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(",".join(columns) + "\n")
        for row in rows:
            f.write(",".join(row) + "\n")


# ---------------- COMPANY ----------------
def save_company(company_data):
    """
    Save or update company data in company.csv.
    """
    ensure_csv_exists(COMPANY_CSV, COMPANY_COLUMNS)
    rows = read_csv(COMPANY_CSV)

    new_rows = []
    updated = False

    for row in rows:
        if row[0] == company_data[0]:
            new_rows.append(company_data)
            updated = True
        else:
            new_rows.append(row)

    if not updated:
        new_rows.append(company_data)

    write_csv(COMPANY_CSV, COMPANY_COLUMNS, new_rows)


def load_company(business_id):
    """
    Load company data by business_id.
    """
    rows = read_csv(COMPANY_CSV)

    if not rows:
        return None

    for row in rows:
        if row[0] == business_id:
            return row
    return None


# ---------------- DECISIONS ----------------
def save_decision(decision_data, year):
    if len(decision_data) != len(DECISION_COLUMNS):
        raise ValueError(
            f"Invalid decision row length: expected {len(DECISION_COLUMNS)}, "
            f"got {len(decision_data)} -> {decision_data}"
        )

    file_path = DECISIONS_CSV_TEMPLATE.format(year=year)
    ensure_csv_exists(file_path, DECISION_COLUMNS)

    rows = read_csv(file_path)
    new_rows = []
    updated = False

    business_id = decision_data[0]
    year_val = str(decision_data[1])
    month_val = str(decision_data[2])
    source = decision_data[-1]

    for row in rows:
        if len(row) != len(DECISION_COLUMNS):
            continue

        if (
            row[0] == business_id
            and row[1] == year_val
            and row[2] == month_val
            and row[-1] == source
        ):
            new_rows.append(decision_data)
            updated = True
        else:
            new_rows.append(row)

    if not updated:
        new_rows.append(decision_data)

    write_csv(file_path, DECISION_COLUMNS, new_rows)


def load_decisions(business_id, year, source="HUMAN"):
    """
    Load decisions for a business/year filtered by decision_source
    """
    file_path = DECISIONS_CSV_TEMPLATE.format(year=year)
    rows = read_csv(file_path)

    decisions_by_month = {}

    for row in rows:
        if row[0] != business_id:
            continue

        row_year = int(row[1])
        row_month = int(row[2])
        row_source = row[-1]

        if row_year != year:
            continue
        if source and row_source != source:
            continue
        decisions_by_month[row_month] = row

    # return sorted by month
    return [decisions_by_month[m] for m in sorted(decisions_by_month)]


# ---------------- RESULTS ----------------
def save_results(results_data, year):
    """
    Save simulation results for a year.
    """
    file_path = RESULTS_CSV_TEMPLATE.format(year=year)
    ensure_csv_exists(file_path, RESULT_COLUMNS)
    write_csv(file_path, RESULT_COLUMNS, results_data)


def load_results(business_id, year):
    """
    Load simulation results for a business/year.
    """
    file_path = RESULTS_CSV_TEMPLATE.format(year=year)
    rows = read_csv(file_path)

    results = []
    for row in rows:
        if row[0] == business_id:
            results.append(row)

    return results


# ---------------- HISTORY ----------------
def save_history(business_id, run_data):
    """
    Save a summary of each simulation run.
    """
    file_path = HISTORY_CSV_TEMPLATE.format(business_id=business_id)
    ensure_csv_exists(file_path, HISTORY_COLUMNS)

    rows = read_csv(file_path)
    rows.append([str(run_data.get(col, "")) for col in HISTORY_COLUMNS])
    write_csv(file_path, HISTORY_COLUMNS, rows)


def load_history(business_id):
    """
    Load run history for a business.
    """
    file_path = HISTORY_CSV_TEMPLATE.format(business_id=business_id)
    rows = read_csv(file_path)

    if not rows:
        return []

    return [dict(zip(HISTORY_COLUMNS, row)) for row in rows]


# ---------------- GOALS ----------------
def set_goal(business_id, goal_runway):
    """
    Save runway goal for a business.
    """
    folder = "data"
    if not os.path.exists(folder):
        os.makedirs(folder)

    file_path = os.path.join(folder, f"goals_{business_id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(goal_runway))


def get_goal(business_id):
    """
    Load runway goal if exists.
    """
    file_path = f"data/goals_{business_id}.txt"
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "r") as f:
            return float(f.read().strip())
    except:
        return None
