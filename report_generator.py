"""
This module handles all formatted console output including:
- Vision boards
- Recommendations
- Histograms
- Comparison reports
"""


def _fmt_runway(x):
    """
    Format runway values safely for CLI / GUI output.
    """
    if x is None:
        return "N/A"
    if isinstance(x, str):
        return x
    try:
        if x == float("inf"):
            return "Stable"
        return f"{float(x):.1f} months"
    except Exception:
        return "N/A"


def print_progress_bar(current, goal, width=40):
    """
    Display a progress bar for runway goal tracking.

    @param current - current runway value
    @param goal - target runway value
    @param width - width of progress bar in characters
    @return None
    """
    if not isinstance(current, (int, float)) or goal <= 0:
        return
    percent = min(current / goal, 1.0)
    filled = int(width * percent)
    bar = "█" * filled + "─" * (width - filled)
    print(f"Runway Goal: [{bar}] {percent*100:.1f}% of {goal} months")


def check_milestones(enriched_rows):
    """
    Check and display milestone achievements.

    @param enriched_rows - analysed simulation results
    @return None
    """
    for row in enriched_rows:
        month = int(row[2])
        profit = float(row[7])
        runway = row[10]

        if profit > 0:
            print(f"Milestone: First profitable month at Month {month}")
            break

        if runway != "Not Losing Money" and float(runway) < 3:
            print("⚠ Warning: Cash runway below 3 months")
            break


def print_vision_board(enriched, company):
    """
    Display business health dashboard with key metrics.

    @param enriched - analysed simulation results
    @param company - Company object
    @return None
    """
    avg_sales = sum(float(r[3]) for r in enriched) / len(enriched)
    avg_profit = sum(float(r[7]) for r in enriched) / len(enriched)

    # Avoid division by zero
    if avg_sales <= 0:
        print("\n===== Business Health Dashboard =====")
        print("Not enough sales data to analyse cost structure.")
        return

    # Cost ratios
    avg_cogs_ratio = sum(float(r[4]) for r in enriched) / len(enriched) / avg_sales
    rent_ratio = company.rent / avg_sales
    staff_ratio = company.staff_cost / avg_sales

    print("\n===== Business Health Dashboard =====")
    print(f"Avg Monthly Sales: RM{avg_sales:,.0f}")
    print(
        f"Avg Monthly {'Profit' if avg_profit >= 0 else 'Loss'}: RM{abs(avg_profit):,.0f}"
    )

    print("\nCost Breakdown (% of sales):")
    print(f"- COGS:  {avg_cogs_ratio * 100:.1f}%")
    print(f"- Rent:  {rent_ratio * 100:.1f}%")
    print(f"- Staff: {staff_ratio * 100:.1f}%")

    # Break-even explanation
    if avg_profit < 0:
        print("\nBiggest Problem:")
        print(f"Sales are roughly RM{abs(avg_profit):,.0f} below break-even per month")


def print_numeric_recommendations(enriched, company):
    """
    Display numeric action recommendations.

    @param enriched - analysed simulation results
    @param company - Company object
    @return None
    """
    avg_profit = sum(float(r[7]) for r in enriched) / len(enriched)
    avg_sales = sum(float(r[3]) for r in enriched) / len(enriched)

    print("\n===== Recommended Actions =====")

    if avg_profit < 0:
        print(f"1. Reduce staff cost 10% → +RM{company.staff_cost * 0.10:,.0f}/month")
        print(f"2. Improve margin 5% → +RM{avg_sales * 0.05:,.0f}/month")
        print(f"3. Increase sales ~RM{abs(avg_profit):,.0f}/month")
    else:
        print(
            f"1. You can reinvest up to RM{avg_profit * 0.5:,.0f}/month "
            f"and still keep a 50% profit safety buffer"
        )

        # Sales buffer before loss
        if avg_sales > 0:
            sales_drop_rm = avg_profit
            sales_drop_pct = (sales_drop_rm / avg_sales) * 100
        else:
            sales_drop_rm = 0
            sales_drop_pct = 0

        print(
            f"2. Sales can drop by about RM{sales_drop_rm:,.0f} "
            f"({sales_drop_pct:.1f}%) before the business becomes loss-making"
        )

        # Marketing headroom
        print(
            f"3. Increasing marketing by up to RM{avg_profit * 0.3:,.0f}/month "
            f"is low risk based on current profitability"
        )


def print_cash_histogram(values, bins=8, width=40):
    """
    Display Monte Carlo ending cash distribution as ASCII histogram
    @param values - list of ending cash values from Monte Carlo runs
    @param bins - number of histogram bins
    @param width - width of bars in characters
    @return None
    """
    if not values:
        return

    bankrupt = sum(1 for v in values if v <= 0)
    total = len(values)

    print("\n===== Ending Cash Distribution (Monte Carlo) =====")
    print(f"Bankruptcy cases: {bankrupt}/{total} ({bankrupt / total * 100:.1f}%)")

    positive = [v for v in values if v > 0]
    if not positive:
        print("All simulations ended in bankruptcy.")
        return

    min_v, max_v = min(positive), max(positive)
    bin_size = (max_v - min_v) / bins if max_v > min_v else max_v or 1

    counts = [0] * bins
    for v in positive:
        idx = min(int((v - min_v) / bin_size), bins - 1)
        counts[idx] += 1

    max_count = max(counts) or 1

    for i in range(bins):
        low = min_v + i * bin_size
        high = low + bin_size
        bar = "█" * int(counts[i] / max_count * width)
        pct = counts[i] / total * 100
        print(f"RM{low:>8,.0f} – RM{high:>8,.0f} | {bar} ({pct:4.1f}%)")


def show_cause_weights(enriched_rows):
    """
    Show which factors contribute most to losses using text bars
    @param enriched_rows - analysed simulation results
    @return top cause identifier string
    """
    totals = {}

    for row in enriched_rows:
        # Safety check: make sure row has index 18
        if len(row) > 18 and row[18]:
            cause_scores_str = row[18]

            if cause_scores_str and cause_scores_str != "":
                pairs = cause_scores_str.split("|")
                for pair in pairs:
                    if ":" in pair:
                        try:
                            k, v = pair.split(":")
                            totals[k] = totals.get(k, 0) + float(v)
                        except ValueError:
                            continue

    if not totals:
        print("No clear loss drivers detected.")
        return "No dominant problem detected"

    print("\n===== Loss Contribution Breakdown =====")
    total_value = sum(totals.values())

    for k, v in sorted(totals.items(), key=lambda x: x[1], reverse=True):
        pct = (v / total_value) * 100 if total_value > 0 else 0
        bar = "█" * int(pct / 5)
        print(f"{k:<12} | {bar} {pct:4.1f}%")

    return max(totals, key=totals.get)


def compare_before_after(before, after):
    """
    Display before/after comparison of key metrics.

    @param before - dict with before metrics
    @param after - dict with after metrics
    @return None
    """
    print("\n===== BEFORE vs AFTER COMPARISON =====")

    print("Avg Monthly Outcome:")
    print(f"  Before: RM{before['avg_profit']:,.0f}")
    print(f"  After : RM{after['avg_profit']:,.0f}")

    print("\nFinal Cash:")
    print(f"  Before: RM{before['final_cash']:,.0f}")
    print(f"  After : RM{after['final_cash']:,.0f}")

    print("\nBankruptcy Risk:")
    print(f"  Before: {before['bankruptcy_prob']:.1f}%")
    print(f"  After : {after['bankruptcy_prob']:.1f}%")

    if after["bankruptcy_prob"] < before["bankruptcy_prob"]:
        print(
            f"\n✅ Risk reduced from "
            f"{before['bankruptcy_prob']:.1f}% → {after['bankruptcy_prob']:.1f}%"
        )
    else:
        print("\n⚠ No meaningful risk reduction detected.")


def compare_risk(before_stats, after_stats):
    """
    Compare bankruptcy risk before and after changes.

    @param before_stats - Monte Carlo stats before change
    @param after_stats - Monte Carlo stats after change
    @return None
    """
    before = before_stats["bankruptcy_prob"]
    after = after_stats["bankruptcy_prob"]

    print("\n===== Risk Comparison =====")
    print(f"Before change : {before:.1f}% bankruptcy risk")
    print(f"After change  : {after:.1f}% bankruptcy risk")

    delta = before - after
    if delta > 0:
        print(f"✅ Risk reduced by {delta:.1f}%")
    else:
        print("⚠ No risk improvement detected")


def print_mc_comparison(before_stats, after_stats):
    """
    Compare Monte Carlo risk before and after a decision.

    Supports:
    - min_runway stats possibly being {} (e.g., all runs stable)
    - stable_runway_prob being present
    """

    print("\n===== Monte Carlo Risk Comparison =====")

    before_risk = before_stats.get("bankruptcy_prob", 0.0)
    after_risk = after_stats.get("bankruptcy_prob", 0.0)

    print("Bankruptcy Risk:")
    print(f"  Before change : {before_risk:.1f}%")
    print(f"  After change  : {after_risk:.1f}%")

    delta = before_risk - after_risk
    if delta > 0:
        print(f"✅ Risk reduced by {delta:.1f}%")
    elif delta < 0:
        print(f"⚠ Risk increased by {abs(delta):.1f}%")
    else:
        print("⚠ No change in risk")

    # Ending cash mean (safe)
    b_cash = before_stats.get("ending_cash", {}).get("mean", 0.0)
    a_cash = after_stats.get("ending_cash", {}).get("mean", 0.0)

    print("\nEnding Cash (Average):")
    print(f"  Before: RM{b_cash:,.0f}")
    print(f"  After : RM{a_cash:,.0f}")

    # NEW: Stable runway probability (if present)
    b_stable = before_stats.get("stable_runway_prob", None)
    a_stable = after_stats.get("stable_runway_prob", None)
    if b_stable is not None or a_stable is not None:
        print("\nStable Runway Probability (no loss months):")
        if b_stable is not None:
            print(f"  Before: {b_stable:.1f}%")
        else:
            print("  Before: N/A")
        if a_stable is not None:
            print(f"  After : {a_stable:.1f}%")
        else:
            print("  After : N/A")

    b_run = before_stats.get("min_runway", {}) or {}
    a_run = after_stats.get("min_runway", {}) or {}

    if b_run or a_run:
        print("\nMinimum Runway (months, only for loss-runs):")
        if b_run:
            print(
                f"  Before median: {_fmt_runway(b_run.get('median'))} | p5: {_fmt_runway(b_run.get('p5'))}"
            )
        else:
            print("  Before median: Stable (all runs) or N/A")

        if a_run:
            print(
                f"  After  median: {_fmt_runway(a_run.get('median'))} | p5: {_fmt_runway(a_run.get('p5'))}"
            )
        else:
            print("  After  median: Stable (all runs) or N/A")


def vision_board_text(enriched, company) -> str:
    avg_sales = sum(float(r[3]) for r in enriched) / len(enriched)
    avg_profit = sum(float(r[7]) for r in enriched) / len(enriched)

    if avg_sales <= 0:
        return (
            "===== Business Health Dashboard =====\n"
            "Not enough sales data to analyse cost structure.\n"
        )

    avg_cogs_ratio = (sum(float(r[4]) for r in enriched) / len(enriched)) / avg_sales
    rent_ratio = company.rent / avg_sales
    staff_ratio = company.staff_cost / avg_sales

    out = []
    out.append("===== Business Health Dashboard =====")
    out.append(f"Avg Monthly Sales: RM{avg_sales:,.0f}")
    out.append(
        f"Avg Monthly {'Profit' if avg_profit >= 0 else 'Loss'}: RM{abs(avg_profit):,.0f}"
    )
    out.append("")
    out.append("Cost Breakdown (% of sales):")
    out.append(f"- COGS:  {avg_cogs_ratio * 100:.1f}%")
    out.append(f"- Rent:  {rent_ratio * 100:.1f}%")
    out.append(f"- Staff: {staff_ratio * 100:.1f}%")

    if avg_profit < 0:
        out.append("")
        out.append("Biggest Problem:")
        out.append(
            f"Sales are roughly RM{abs(avg_profit):,.0f} below break-even per month"
        )

    return "\n".join(out) + "\n"


def numeric_recommendations_text(enriched, company) -> str:
    avg_profit = sum(float(r[7]) for r in enriched) / len(enriched)
    avg_sales = sum(float(r[3]) for r in enriched) / len(enriched)

    out = []
    out.append("===== Recommended Actions =====")

    if avg_profit < 0:
        out.append(
            f"1. Reduce staff cost 10% → +RM{company.staff_cost * 0.10:,.0f}/month"
        )
        out.append(f"2. Improve margin 5% → +RM{avg_sales * 0.05:,.0f}/month")
        out.append(f"3. Increase sales ~RM{abs(avg_profit):,.0f}/month")
    else:
        out.append(
            f"1. You can reinvest up to RM{avg_profit * 0.5:,.0f}/month "
            f"and still keep a 50% profit safety buffer"
        )
        sales_drop_rm = avg_profit
        sales_drop_pct = (sales_drop_rm / avg_sales) * 100 if avg_sales > 0 else 0
        out.append(
            f"2. Sales can drop by about RM{sales_drop_rm:,.0f} "
            f"({sales_drop_pct:.1f}%) before the business becomes loss-making"
        )
        out.append(
            f"3. Increasing marketing by up to RM{avg_profit * 0.3:,.0f}/month "
            f"is low risk based on current profitability"
        )

    return "\n".join(out) + "\n"
