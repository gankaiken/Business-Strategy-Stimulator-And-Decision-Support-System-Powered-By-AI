"""
This file defines all CSV file names and column structures to ensure they all are in the same data format
"""

# Core CSVs
COMPANY_CSV = "data/company.csv"
DECISIONS_CSV_TEMPLATE = "data/decisions_{year}.csv"
RESULTS_CSV_TEMPLATE = "data/results_{year}.csv"
MARKET_CSV = "data/market.csv"
HISTORY_CSV_TEMPLATE = "data/history_{business_id}.csv"
SCENARIO_CSV_TEMPLATE = "data/scenarios_{business_id}_{year}.csv"

RUNWAY_IDX = 10
HEALTH_IDX = 11
PROFIT_IDX = 7

COMPANY_COLUMNS = [
    "business_id",
    "business_type",
    "starting_cash",
    "baseline_sales",
    "baseline_cogs",
    "rent",
    "staff_cost",
    "utilities",
    "subscriptions",
    "loan_payment",
    "other_fixed",
]
"""
Purpose:
Defines the columns required to describe a business baseline profile.
Why these fields exist:
- business_id        : uniquely identifies a business
- business_type      : restaurant or grocery (used for benchmarks)
- starting_cash      : used to calculate survival runway
- baseline_sales     : normal monthly sales before decisions
- baseline_cogs      : normal monthly cost of goods
- rent               : fixed cost (often a major loss driver)
- staff_cost         : fixed cost
- utilities          : fixed cost
- subscriptions      : fixed cost (POS, software, etc.)
- loan_payment       : debt obligation
- other_fixed        : any other recurring fixed cost
"""

DECISION_COLUMNS = [
    "business_id",
    "year",
    "month",
    "price_change_pct",
    "marketing_spend",
    "staff_cost_adjustment",
    "waste_reduction_pct",
    "inventory_tightness",
    "decision_source",
]
"""
Purpose:
Defines the monthly decisions made by the user for each month (1–12).
Why these fields exist:
- business_id            : links decision to a business
- year                   : allows multi-year simulations
- month                  : 1 to 12 (editable anytime)
- price_change_pct       : user changes pricing strategy
- marketing_spend        : user marketing decision
- staff_cost_adjustment  : increase or reduce staff cost
- waste_reduction_pct    : efficiency improvement (COGS reduction)
- inventory_tightness    : controls spoilage (mainly grocery)
"""

RESULT_COLUMNS = [
    "business_id",
    "year",
    "month",
    "sales",
    "cogs",
    "fixed_costs",
    "marketing_spend",
    "profit",
    "cash_end",
    "gross_margin",
    "runway_months",
    "health_flag",
    "causes",
    "suggestions",
    "be_status",
    "biggest_lever",
    "monthly_summary",
    "root_cause",
    "readiness_flag",
    "cause_scores",
]
"""
Purpose:
Stores simulation output and decision-support insights for each month.
Why these fields exist:
- sales: revenue for the month
- cogs: cost of goods sold
- fixed_costs: total fixed expenses
- marketing_spend: marketing cost for the month
- profit: profit or loss
- cash_end: remaining cash after the month
- gross_margin: sales efficiency indicator
- runway_months: how long the business can survive
- health_flag: GREEN / YELLOW / RED
- causes: reasons for profit or loss
- suggestions: actions to take next
- be_status: break-even status
- biggest_lever: biggest potential impact lever
NEW:
- monthly_summary: human-friendly one-line explanation
- root_cause: top root cause label derived from user's data
- readiness_flag: expansion readiness if profitable
- cause_scores: compact string of cause impact scores for plots
"""

HISTORY_COLUMNS = [
    "date",
    "run_datetime",
    "decision_source",
    "total_profit",
    "ending_cash",
    "min_runway",
    "health_mostly",
    "notes",
]

SCENARIO_COLUMNS = [
    "scenario_name",
    "run_datetime",
    "total_profit",
    "ending_cash",
    "min_runway",
    "health_mostly",
    "readiness_flag",
    "top_root_cause",
    "status",
    "notes",
]


def is_valid_month(month):
    """
    Check whether a month value is valid (1 to 12).
    @param month - the month number to check
    @return bool - True if valid, False otherwise
    """
    return isinstance(month, int) and 1 <= month <= 12


def is_valid_business_type(business_type):
    """
    Check whether the business type is supported.
    @param business_type - type of business as a string
    @return bool - True if business type is valid
    """
    return business_type in ["restaurant", "grocery"]
