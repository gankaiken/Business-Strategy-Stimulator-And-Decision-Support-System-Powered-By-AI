# Business Strategy Simulator And Decision Support System Powered By AI

Video Demo: [https://monashuni-my.sharepoint.com/:v:/g/personal/kgan0031_student_monash_edu/IQAC5qTSW1AyQanNPHMr5feMAVtehjBi8trJ4SJKLOP5sdA?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=nb9IdJ]

A comprehensive financial planning and decision support tool for small businesses (restaurants and grocery stores). Simulates 12 months of operations, diagnoses root causes of profit/loss, and quantifies bankruptcy risk using Monte Carlo simulation.

## Features

### 1. **Monthly Business Simulation**
- Calculates sales based on pricing, marketing, and seasonality
- Models cost of goods sold (COGS) with waste reduction and spoilage
- Tracks cash flow and runway (months until bankruptcy)
- Assigns health flags: GREEN (safe), YELLOW (caution), RED (critical)

### 2. **Monte Carlo Risk Analysis** 
- Runs 500+ simulations with randomized demand
- Computes bankruptcy probability (e.g., "8.2% chance of failure")
- Shows distribution of possible outcomes (best-case, worst-case, median)
- Custom implementation without NumPy/SciPy

### 3. **AI Strategy Optimization** 
- Genetic Algorithm searches thousands of strategies (150 generations)
- Optimizes pricing, marketing, staffing, and efficiency decisions
- Balances profitability (70%) with cash safety (20%) and bankruptcy risk
- Fully custom—no external AI libraries used

### 4. **Root Cause Diagnosis**
- Compares performance to industry benchmarks (gross margin, rent ratios)
- Identifies specific problems: "Low margin costs RM500/month"
- Ranks causes by impact (e.g., "Margin issue 43%, Rent 24%")
- Generates actionable recommendations

### 5. **Sensitivity Analysis**
- Tests which decision lever affects profit most
- Ranks: pricing, marketing, staffing, waste reduction
- Example: "Marketing spend has 2× more impact than pricing"

### 6. **Dual User Interfaces**
- **CLI**: Step-by-step guided explanations (best for learning)
- **GUI**: Interactive exploration with charts and drill-downs (11 pages)
- Both share 90% of backend logic (no code duplication)

### 7. **Professional Outputs**
- Matplotlib charts: profit trends, cash flow, Monte Carlo histograms
- PDF export for AI-optimized strategies
- Scenario comparison (before vs. after decisions)
- Run history tracking

## Installation

**Requirements:** Python 3.8+
```bash
pip install matplotlib reportlab splashkit
```

## Quick Start
```bash
python main.py
```

Choose CLI (option 1) or GUI (option 2).

**First-Time Setup:**
1. Enter User ID, Business ID, and Year
2. Fill `data/company.csv` with business baseline (sales, costs, cash)
3. Fill `data/decisions_YEAR.csv` with 12 months of decisions
4. Run **Full Business Analysis** to simulate and view results

## CSV Format Examples

**company.csv:**
```csv
business_id,business_type,starting_cash,baseline_sales,baseline_cogs,rent,staff_cost,utilities,subscriptions,loan_payment,other_fixed
my_cafe,restaurant,50000,45000,18000,8000,12000,1500,500,2000,1000
```

**decisions_2024.csv:**
```csv
business_id,year,month,price_change_pct,marketing_spend,staff_cost_adjustment,waste_reduction_pct,inventory_tightness,decision_source
my_cafe,2024,1,0.00,1500,0,0.05,0.8,HUMAN
my_cafe,2024,2,0.00,1500,0,0.05,0.8,HUMAN
...
```

## Key Algorithms (Custom Implementations)

- **Monte Carlo Simulation**: 500+ runs, manual percentile calculation
- **Genetic Algorithm**: Tournament selection, crossover, mutation, elitism
- **Insertion Sort**: Custom sorting with key functions

## Project Structure

24 Python files organized in 5 layers:
- **Data Layer**: CSV/JSON I/O, schemas
- **Models**: Company, Decision, Market classes
- **Logic**: Simulation, Analysis, Optimization
- **Controllers**: Orchestrate workflows (CLI + GUI)
- **Presentation**: Visualizations, reports, interfaces

## Testing
```bash
python test.py
```

Runs 20 unit tests covering simulation, analysis, sorting, and market logic.

