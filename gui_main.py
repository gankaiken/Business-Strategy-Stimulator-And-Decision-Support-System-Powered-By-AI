import tkinter as tk
from tkinter import messagebox
import threading
import os
from gui_components import THEME, ToolTip
from schemas import (
    COMPANY_CSV,
    DECISIONS_CSV_TEMPLATE,
    COMPANY_COLUMNS,
    DECISION_COLUMNS,
)
from simulation_controller import run_full_analysis_workflow_gui
from data_io import (
    ensure_csv_exists,
    load_results,
    load_decisions,
    save_decision,
    get_goal,
    set_goal,
    load_history,   
    load_company,
)
from business_helpers import company_row_to_object, decision_rows_to_objects
from market import create_default_market
from simulation import BusinessSimulator
from sensitivity import run_sensitivity
from optimizer import GeneticOptimizer
from user_profiles import (
    ensure_user_exists,
    ensure_business_exists,
    ensure_year_exists,
)
from report import export_ai_strategy_to_pdf
import sys, os, subprocess


D_BID = 0
D_YEAR = 1
D_MONTH = 2
D_PRICE = 3
D_MKT = 4
D_STAFF = 5
D_WASTE = 6
D_INV = 7

class BusinessSimulatorGUI:
    def __init__(self, on_exit=None):
        self.on_exit = on_exit
        self.root = tk.Tk()
        self.root.title("Business Strategy Simulator (GUI)")
        self.root.geometry("1100x700")
        self.root.configure(bg=THEME["bg"])

        self.business_id = None
        self.year = None
        self.decision_source = "HUMAN"
        self._exit_handler = None
        self.last_report_path = None

        self.container = tk.Frame(self.root, bg=THEME["bg"])
        self.container.pack(fill="both", expand=True)

        self.pages = {}
        for PageCls in (
            SetupPage,
            MenuPage,
            QuickHealthPage,
            FullAnalysisPage,
            EditDecisionsPage,
            SetSurvivalGoalPage,
            ReviewPastRunsPage,
            SensitivityTestPage,
            IntelligentAdvisorPage,
            CompareRunsPage,
            ExportPDFPage,
            PlaceholderPage,
        ):
            page = PageCls(self)
            self.pages[PageCls.__name__] = page
            page.frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show("SetupPage")

    def set_exit_handler(self, fn):
        self._exit_handler = fn

    def show(self, page_name):
        self.pages[page_name].frame.lift()
        self.pages[page_name].on_show()

    def ensure_files_exist(self):
        if not os.path.exists(COMPANY_CSV):
            ensure_csv_exists(COMPANY_CSV, COMPANY_COLUMNS)
            messagebox.showinfo("Setup Needed", "company.csv created. Please fill it first.")
            return False

        decisions_csv = DECISIONS_CSV_TEMPLATE.format(year=self.year)
        if not os.path.exists(decisions_csv):
            ensure_csv_exists(decisions_csv, DECISION_COLUMNS)
            messagebox.showinfo("Setup Needed", f"{decisions_csv} created. Please fill it first.")
            return False

        return True

    def exit_app(self):
        if self._exit_handler:
            self._exit_handler()
        else:
            self.root.destroy()

    def run(self):
        self.root.mainloop()


class BasePage:
    def __init__(self, app: BusinessSimulatorGUI):
        self.app = app
        self.frame = tk.Frame(app.container, bg=THEME["bg"])

    def on_show(self):
        pass


class SetupPage(BasePage):
    def __init__(self, app):
        super().__init__(app)

        card = tk.Frame(
            self.frame,
            bg=THEME["panel"],
            highlightthickness=1,
            highlightbackground="#22313F",
        )
        card.place(relx=0.5, rely=0.5, anchor="center", width=540, height=400)

        tk.Label(
            card,
            text="User / Business / Year Setup",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 18, "bold"),
        ).pack(pady=(22, 10))

        tk.Label(
            card,
            text="Enter your User ID, Business ID, and Year to begin.",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 11),
        ).pack(pady=(0, 18))

        form = tk.Frame(card, bg=THEME["panel"])
        form.pack()

        # USER ID FIELD
        tk.Label(
            form,
            text="User ID",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 11),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=10)
        self.user = tk.Entry(form, width=30)
        self.user.grid(row=0, column=1, padx=12, pady=10)

        # BUSINESS ID FIELD
        tk.Label(
            form,
            text="Business ID",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 11),
        ).grid(row=1, column=0, sticky="w", padx=12, pady=10)
        self.bid = tk.Entry(form, width=30)
        self.bid.grid(row=1, column=1, padx=12, pady=10)

        # YEAR FIELD
        tk.Label(
            form,
            text="Year",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 11),
        ).grid(row=2, column=0, sticky="w", padx=12, pady=10)
        self.year = tk.Entry(form, width=30)
        self.year.grid(row=2, column=1, padx=12, pady=10)

        btns = tk.Frame(card, bg=THEME["panel"])
        btns.pack(pady=(18, 0))

        tk.Button(
            btns,
            text="Continue",
            bg=THEME["accent"],
            fg="black",
            relief="flat",
            padx=18,
            pady=10,
            command=self.continue_to_menu,
        ).pack(side="left", padx=8)

        tk.Button(
            btns,
            text="Exit",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=18,
            pady=10,
            command=self.app.exit_app,
        ).pack(side="left", padx=8)

    def continue_to_menu(self):
        user_id = self.user.get().strip()
        business_id = self.bid.get().strip()
        y = self.year.get().strip()

        if not user_id:
            messagebox.showwarning("Missing", "Please enter User ID.")
            return

        if not business_id:
            messagebox.showwarning("Missing", "Please enter Business ID.")
            return

        if not y:
            messagebox.showwarning("Missing", "Please enter Year.")
            return

        try:
            year = int(y)
        except ValueError:
            messagebox.showwarning("Invalid", "Year must be a number.")
            return

        try:
            ensure_user_exists(user_id)
            ensure_business_exists(user_id, business_id)
            ensure_year_exists(user_id, business_id, year)

        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        self.app.business_id = business_id
        self.app.year = year

        if not self.app.ensure_files_exist():
            return

        self.app.show("MenuPage")


class MenuPage(BasePage):
    def __init__(self, app):
        super().__init__(app)

        header = tk.Frame(self.frame, bg=THEME["bg"])
        header.pack(fill="x", padx=24, pady=18)

        tk.Label(
            header,
            text="Main Menu",
            bg=THEME["bg"],
            fg=THEME["text"],
            font=("Segoe UI", 20, "bold"),
        ).pack(side="left")

        self.ctx = tk.Label(
            header, text="", bg=THEME["bg"], fg=THEME["muted"], font=("Segoe UI", 11)
        )
        self.ctx.pack(side="right")

        card = tk.Frame(
            self.frame,
            bg=THEME["panel"],
            highlightthickness=1,
            highlightbackground="#22313F",
        )
        card.pack(fill="both", expand=True, padx=24, pady=12)

        left = tk.Frame(card, bg=THEME["panel"])
        left.pack(side="left", fill="y", padx=18, pady=18)

        right = tk.Frame(card, bg=THEME["panel"])
        right.pack(side="left", fill="both", expand=True, padx=18, pady=18)

        tk.Label(
            left,
            text="Options",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w", pady=(0, 12))

        self.help = tk.Label(
            right,
            text="Hover over an option to see what it does.",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 12),
            justify="left",
            wraplength=600,
        )
        self.help.pack(anchor="nw")

        menu = [
            (
                "0. Quick Health Check",
                "Get a fast snapshot of your business health based on the latest saved simulation. "
                "This shows whether your business is profitable, how long your cash can last (runway), "
                "and whether the overall situation is stable, risky, or critical. "
                "Useful for quick decision-making without running a full analysis.",
                "QuickHealthPage",
            ),
            (
                "1. Run Full Business Analysis",
                "Run a complete 12-month simulation of your business using your current decisions. "
                "This analysis projects monthly profit or loss, cash balance, runway, and risk level, "
                "and includes uncertainty testing to show best- and worst-case outcomes. "
                "Use this to understand how your business may perform over the year.",
                "FullAnalysisPage",
            ),
            (
                "2. Edit Monthly Decisions",
                "Review and adjust your business decisions for each month, including pricing changes, "
                "marketing spending, staff cost adjustments, waste reduction, and inventory control. "
                "These inputs directly affect how the simulation behaves and allow you to test different strategies.",
                "EditDecisionsPage",
            ),
            (
                "3. Set Survival Goal",
                "Set a target for how many months your business should survive based on available cash. "
                "This feature compares your actual cash runway against your goal and highlights potential risk. "
                "It also allows simple what-if scenarios to see how changes in cash or losses affect survival.",
                "SetSurvivalGoalPage",
            ),
            (
                "4. Review Past Runs",
                "Review and compare results from previous simulation runs. "
                "This helps you identify which strategies performed best or worst in terms of profit, "
                "cash flow, and risk, and supports learning from past decisions.",
                "ReviewPastRunsPage",
            ),
            (
                "5. Sensitivity Test",
                "Discover which business decisions have the biggest impact on profit. "
                "This test adjusts one decision at a time and measures how strongly it affects outcomes, "
                "helping you focus on the most influential levers instead of changing everything at once.",
                "SensitivityTestPage",
            ),
            (
                "6. Intelligent Advisor",
                "Use an AI-powered optimizer to automatically search for better business strategies. "
                "The system tests many combinations of monthly decisions and recommends a plan that aims "
                "to improve profit while reducing the risk of running out of cash.",
                "IntelligentAdvisorPage",
            ),
            (
                "7. Compare Before vs After (Runs)",
                "Compare your most recent AI-generated strategy against your previous human-made strategy. "
                "This view highlights changes in profit, cash position, and runway, helping you decide "
                "whether the AI recommendations improved your business performance.",
                "CompareRunsPage",
            ),
            (
                "8. Export AI Strategy (PDF)",
                "Generate a professional PDF report summarising the AI-recommended business strategy. "
                "The report includes an executive summary, projected profit, cash runway, risk level, "
                "and a detailed 12-month action plan. "
                "Ideal for documentation, assessment submission, or sharing with stakeholders.",
                "ExportPDFPage",
            ),
            (
                "9. Exit",
                "Exit the application safely and return to the main program or desktop.",
                "EXIT",
            ),
        ]

        for label, summary, target in menu:
            btn = tk.Button(
                left,
                text=label,
                anchor="w",
                width=30,
                bg="#22313F",
                fg=THEME["text"],
                relief="flat",
                padx=12,
                pady=10,
                command=lambda t=target: self.pick(t),
            )
            btn.pack(fill="x", pady=6)
            btn.bind("<Enter>", lambda e, s=summary: self.help.config(text=s))
            ToolTip(btn, summary)

    def on_show(self):
        self.ctx.config(
            text=f"Business: {self.app.business_id} | Year: {self.app.year}"
        )

    def pick(self, target):
        if target == "EXIT":
            self.app.exit_app()
            return
        self.app.show(target)


class QuickHealthPage(BasePage):
    def __init__(self, app):
        super().__init__(app)

        top = tk.Frame(self.frame, bg=THEME["bg"])
        top.pack(fill="x", padx=24, pady=18)

        tk.Label(
            top,
            text="Quick Health Check",
            bg=THEME["bg"],
            fg=THEME["text"],
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")

        tk.Button(
            top,
            text="Back",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=14,
            pady=8,
            command=lambda: self.app.show("MenuPage"),
        ).pack(side="right")

        panel = tk.Frame(
            self.frame,
            bg=THEME["panel"],
            highlightthickness=1,
            highlightbackground="#22313F",
        )
        panel.pack(fill="both", expand=True, padx=24, pady=12)

        self.out = tk.Label(
            panel,
            text="",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12),
            justify="left",
            wraplength=900,
        )
        self.out.pack(anchor="nw", padx=18, pady=18)

    def on_show(self):
        bid, year = self.app.business_id, self.app.year
        results = load_results(bid, year)

        if not results:
            self.out.config(
                text="No previous results found.\n\nRun Full Business Analysis first."
            )
            return

        last = results[-1]
        profit = None
        try:
            profit = float(last[7])
        except:
            pass

        runway = last[10] if len(last) > 10 else "N/A"
        health = last[11] if len(last) > 11 else "N/A"
        month = last[2] if len(last) > 2 else "N/A"

        msg = (
            f"Last recorded month: {month}\n"
            f"Profit/Loss: {'RM{:,.0f}'.format(profit) if profit is not None else 'N/A'}\n"
            f"Cash Runway: {runway}\n"
            f"Health: {health}\n\n"
        )

        if health == "RED":
            msg += "⚠ Recommended: Run Full Business Analysis"
        elif health == "YELLOW":
            msg += "⚠ Recommended: Monitor closely or test improvements"
        else:
            msg += "✅ Business appears stable"

        self.out.config(text=msg)


class FullAnalysisPage(BasePage):

    def __init__(self, app):
        super().__init__(app)
        self.enriched = []
        self.payload = None
        self.plotters = {}

        top = tk.Frame(self.frame, bg=THEME["bg"])
        top.pack(fill="x", padx=24, pady=18)

        tk.Label(
            top,
            text="Full Business Analysis",
            bg=THEME["bg"],
            fg=THEME["text"],
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")

        tk.Button(
            top,
            text="Back",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=14,
            pady=8,
            command=lambda: self.app.show("MenuPage"),
        ).pack(side="right")


        panel = tk.Frame(
            self.frame,
            bg=THEME["panel"],
            highlightthickness=1,
            highlightbackground="#22313F",
        )
        panel.pack(fill="both", expand=True, padx=24, pady=12)
        report_wrap = tk.Frame(panel, bg=THEME["panel"])
        report_wrap.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        tk.Label(
            report_wrap,
            text="Report Output (CLI style)",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(0, 6))

        report_body = tk.Frame(report_wrap, bg=THEME["panel"])
        report_body.pack(fill="both", expand=True)

        self.report_text = tk.Text(
            report_body,
            height=14,
            wrap="word",
            bg="#22313F",
            fg=THEME["text"],
            insertbackground=THEME["text"],
            relief="flat",
            padx=12,
            pady=12,
        )
        self.report_text.pack(side="left", fill="both", expand=True)

        scroll = tk.Scrollbar(report_body, command=self.report_text.yview)
        scroll.pack(side="right", fill="y")
        self.report_text.configure(yscrollcommand=scroll.set)
        self.report_text.config(state="disabled")
        self.status = tk.Label(
            panel,
            text="Click Run to start.",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 12),
        )
        self.status.pack(anchor="nw", padx=18, pady=(12, 6))
        strategy_wrap = tk.Frame(panel, bg=THEME["panel"])
        strategy_wrap.pack(anchor="nw", padx=18, pady=(0, 6))

        tk.Label(
            strategy_wrap,
            text="Strategy:",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=(0, 12))

        self.strategy_var = tk.StringVar(value="HUMAN")

        tk.Radiobutton(
            strategy_wrap,
            text="My Decisions",
            variable=self.strategy_var,
            value="HUMAN",
            bg=THEME["panel"],
            fg=THEME["text"],
            selectcolor=THEME["panel"],
            activebackground=THEME["panel"],
            command=self._update_strategy,
        ).pack(side="left", padx=6)

        tk.Radiobutton(
            strategy_wrap,
            text="AI Decisions",
            variable=self.strategy_var,
            value="AI",
            bg=THEME["panel"],
            fg=THEME["text"],
            selectcolor=THEME["panel"],
            activebackground=THEME["panel"],
            command=self._update_strategy,
        ).pack(side="left", padx=6)


        self.run_btn = tk.Button(
            panel,
            text="Run Analysis",
            bg=THEME["accent"],
            fg="black",
            relief="flat",
            padx=14,
            pady=8,
            command=self.run_analysis,
        )
        self.run_btn.pack(anchor="nw", padx=18, pady=(0, 10))

        self.progress_canvas = tk.Canvas(
            panel, width=420, height=18, bg=THEME["panel"], highlightthickness=0
        )
        self.progress_canvas.pack(anchor="nw", padx=18, pady=(0, 4))

        self.progress_lbl = tk.Label(
            panel,
            text="",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 10),
        )
        self.progress_lbl.pack(anchor="nw", padx=18, pady=(0, 10))

        self.mc_stats_lbl = tk.Label(
            panel,
            text="",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 11),
            justify="left",
            wraplength=980,
        )
        self.mc_stats_lbl.pack(anchor="nw", padx=18, pady=(0, 12))

        charts_row = tk.Frame(panel, bg=THEME["panel"])
        charts_row.pack(anchor="nw", padx=18, pady=(0, 12))

        self.chart_buttons = {}
        for key, label in [
            ("dashboard", "Dashboard"),
            ("cash", "Cash"),
            ("profit", "Profit"),
            ("sales", "Sales"),
            ("cost", "Cost"),
            ("mc_hist", "MC Histogram"),
        ]:
            b = tk.Button(
                charts_row,
                text=label,
                bg="#22313F",
                fg=THEME["text"],
                relief="flat",
                padx=12,
                pady=6,
                state="disabled",
                command=lambda k=key: self.show_chart(k),
            )
            b.pack(side="left", padx=6)
            self.chart_buttons[key] = b

        body = tk.Frame(panel, bg=THEME["panel"])
        body.pack(fill="both", expand=True, padx=18, pady=18)

        self.months = tk.Listbox(body, width=35, height=18)
        self.months.pack(side="left", fill="y")
        self.months.bind("<<ListboxSelect>>", self.select_month)

        self.detail = tk.Label(
            body,
            text="",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12),
            justify="left",
            wraplength=650,
        )
        self.detail.pack(side="left", fill="both", expand=True, padx=18)

    def _update_strategy(self):
        self.app.decision_source = self.strategy_var.get()

    def run_analysis(self):
        bid, year = self.app.business_id, self.app.year

        self.status.config(text="Running analysis…")
        self.months.delete(0, tk.END)
        self.detail.config(text="")
        self.mc_stats_lbl.config(text="")
        self.plotters = {}

        self._report_set("")
        self._draw_progress(0.0)
        self.progress_lbl.config(text="")
        self.run_btn.config(state="disabled")

        for b in self.chart_buttons.values():
            b.config(state="disabled")

        def progress_callback(done, total=None):
            total = total or 500
            ratio = min(done / total, 1.0)
            self.frame.after(0, lambda: self._draw_progress(ratio))
            self.frame.after(0, lambda: self.progress_lbl.config(text=f"Monte Carlo: {done}/{total}"))

        def log_callback(msg):
            self.frame.after(0, lambda m=msg: self._report_append(m))

        def worker():
            try:
                payload = run_full_analysis_workflow_gui(
                    business_id=bid,
                    year=year,
                    decision_source=self.app.decision_source, 
                    num_mc_runs=500,
                    progress_callback=progress_callback,
                    log_callback=log_callback,
                )
                
                self.frame.after(0, lambda: self._draw_progress(1.0))
                self.frame.after(0, lambda: self.progress_lbl.config(text="Monte Carlo: 500/500"))

                self.payload = payload
                self.enriched = payload.get("enriched", [])
                self.plotters = payload.get("plotters", {}) or {}

                self.frame.after(0, self.populate)
                self.frame.after(0, lambda: self._render_mc_stats(payload.get("mc_stats")))
                self.frame.after(0, self._enable_charts)
                self.frame.after(
                    0,
                    lambda: self.status.config(
                        text="Done. Select a month for details."
                    ),
                )

            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.frame.after(0, lambda: self.status.config(text="Failed."))

            finally:
                self.frame.after(0, lambda: self.run_btn.config(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def _enable_charts(self):
        for k, btn in self.chart_buttons.items():
            btn.config(state=("normal" if k in self.plotters else "disabled"))

    def populate(self):
        self.months.delete(0, tk.END)
        for r in self.enriched:
            month = r[2]
            profit = float(r[7])
            health = r[11]
            self.months.insert(tk.END, f"Month {month} | {health} | RM{profit:,.0f}")

    def select_month(self, _=None):
        sel = self.months.curselection()
        if not sel:
            return

        r = self.enriched[sel[0]]
        self.detail.config(
            text=(
                f"Month {r[2]}\n\n"
                f"Health: {r[11]}\n"
                f"Profit/Loss: RM{float(r[7]):,.0f}\n"
                f"Cash End: RM{float(r[8]):,.0f}\n"
                f"Runway: {r[10]}\n\n"
                f"What happened:\n{r[16]}"
            )
        )

    def _draw_progress(self, ratio):
        c = self.progress_canvas
        c.delete("all")
        ratio = max(0.0, min(1.0, ratio))
        c.create_rectangle(0, 0, 420, 18, fill="#22313F", outline="#22313F")
        c.create_rectangle(
            0, 0, int(420 * ratio), 18, fill=THEME["accent"], outline=THEME["accent"]
        )
        c.create_text(
            210, 9, text=f"{ratio*100:.0f}%", fill="black", font=("Segoe UI", 9, "bold")
        )

    def _render_mc_stats(self, mc_stats):
        if not mc_stats:
            return

        text = (
            "===== Monte Carlo Summary =====\n"
            f"Bankruptcy probability: {mc_stats.get('bankruptcy_prob', 0):.1f}%\n"
            f"Chance of positive yearly profit: {mc_stats.get('positive_profit_prob', 0):.1f}%\n"
            f"Average RED months (runway < 1.5): {mc_stats.get('avg_red_months', 0):.2f}\n"
        )
        self.mc_stats_lbl.config(text=text)

    def show_chart(self, key):
        fn = self.plotters.get(key)
        if fn:
            fn()

    def _report_set(self, text):
        self.report_text.config(state="normal")
        self.report_text.delete("1.0", "end")
        self.report_text.insert("end", text)
        self.report_text.see("end")
        self.report_text.config(state="disabled")

    def _report_append(self, line):
        self.report_text.config(state="normal")
        self.report_text.insert("end", str(line) + "\n")
        self.report_text.see("end")
        self.report_text.config(state="disabled")


# OPTION 2: EDIT DECISIONS (GUI)
class EditDecisionsPage(BasePage):
    def __init__(self, app):
        super().__init__(app)

        self.decisions_by_month = {} 

        top = tk.Frame(self.frame, bg=THEME["bg"])
        top.pack(fill="x", padx=24, pady=18)

        tk.Label(
            top,
            text="Edit Monthly Decisions",
            bg=THEME["bg"],
            fg=THEME["text"],
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")

        tk.Button(
            top,
            text="Back",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=14,
            pady=8,
            command=lambda: self.app.show("MenuPage"),
        ).pack(side="right")

        panel = tk.Frame(
            self.frame,
            bg=THEME["panel"],
            highlightthickness=1,
            highlightbackground="#22313F",
        )
        panel.pack(fill="both", expand=True, padx=24, pady=12)

        self.status = tk.Label(
            panel,
            text="Select a month to edit. Then click Save.",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 12),
        )
        self.status.pack(anchor="nw", padx=18, pady=(18, 10))

        body = tk.Frame(panel, bg=THEME["panel"])
        body.pack(fill="both", expand=True, padx=18, pady=18)

        # Left: months list
        left = tk.Frame(body, bg=THEME["panel"])
        left.pack(side="left", fill="y")

        tk.Label(
            left,
            text="Months",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        self.months = tk.Listbox(left, width=18, height=18)
        self.months.pack(fill="y")
        self.months.bind("<<ListboxSelect>>", self.on_select_month)

        # Right: form
        right = tk.Frame(body, bg=THEME["panel"])
        right.pack(side="left", fill="both", expand=True, padx=(18, 0))

        tk.Label(
            right,
            text="Decision Editor",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.entries = {}

        def add_field(r, label, hint):
            tk.Label(
                right,
                text=label,
                bg=THEME["panel"],
                fg=THEME["text"],
                font=("Segoe UI", 11),
            ).grid(row=r, column=0, sticky="w", padx=(0, 10), pady=8)
            e = tk.Entry(right, width=28)
            e.grid(row=r, column=1, sticky="w", pady=8)
            ToolTip(e, hint)
            self.entries[label] = e

        add_field(
            1,
            "Price change (%)",
            "Example: 5 means +5% price, -5 means discount 5%. Range suggestion: -100 to 100.",
        )
        add_field(2, "Marketing spend (RM)", "Example: 2000. Must be 0 or more.")
        add_field(
            3,
            "Staff cost adjustment (RM)",
            "Positive increases staff cost; negative reduces. Example: -300.",
        )
        add_field(
            4,
            "Waste reduction (%)",
            "Efficiency improvement (COGS reduction). Example: 5 = 5%. Suggest 0 to 100.",
        )
        add_field(
            5,
            "Inventory tightness (0–1)",
            "Controls inventory level. 0 = loose, 1 = very tight. Must be between 0 and 1.",
        )

        btns = tk.Frame(right, bg=THEME["panel"])
        btns.grid(row=6, column=0, columnspan=2, sticky="w", pady=(14, 0))

        tk.Button(
            btns,
            text="Save",
            bg=THEME["accent"],
            fg="black",
            relief="flat",
            padx=16,
            pady=10,
            command=self.save_current,
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btns,
            text="Reset Month",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=16,
            pady=10,
            command=self.reset_current,
        ).pack(side="left")

        self.current_month = None

    def on_show(self):
        bid, year = self.app.business_id, self.app.year
        rows = load_decisions(bid, year, source="HUMAN")

        self.decisions_by_month = {}
        for r in rows:
            try:
                m = int(r[D_MONTH])
            except:
                continue
            self.decisions_by_month[m] = r

        self.months.delete(0, tk.END)
        for m in range(1, 13):
            tag = "✅" if m in self.decisions_by_month else "—"
            self.months.insert(tk.END, f"Month {m:02d}  {tag}")

        self.status.config(
            text="Select a month to edit. ✅ means a decision exists for that month."
        )
        self.current_month = None
        self._clear_form()

    def _clear_form(self):
        for e in self.entries.values():
            e.delete(0, tk.END)

    def on_select_month(self, _=None):
        sel = self.months.curselection()
        if not sel:
            return

        text = self.months.get(sel[0])
        try:
            month = int(text.split()[1])
        except:
            return

        self.current_month = month
        row = self.decisions_by_month.get(month)

        if row:
            vals = {
                "Price change (%)": row[D_PRICE],
                "Marketing spend (RM)": row[D_MKT],
                "Staff cost adjustment (RM)": row[D_STAFF],
                "Waste reduction (%)": row[D_WASTE],
                "Inventory tightness (0–1)": row[D_INV],
            }
            self.status.config(
                text=f"Editing Month {month}. Loaded existing decision ✅"
            )
        else:
            vals = {
                "Price change (%)": "0",
                "Marketing spend (RM)": "0",
                "Staff cost adjustment (RM)": "0",
                "Waste reduction (%)": "0",
                "Inventory tightness (0–1)": "0.50",
            }
            self.status.config(
                text=f"Editing Month {month}. No decision yet — defaults loaded."
            )

        for k, v in vals.items():
            e = self.entries[k]
            e.delete(0, tk.END)
            e.insert(0, str(v))

    def reset_current(self):
        if self.current_month is None:
            messagebox.showwarning("No month selected", "Please select a month first.")
            return
        # Reload same month values (existing or defaults)
        self.on_select_month()

    def save_current(self):
        if self.current_month is None:
            messagebox.showwarning("No month selected", "Please select a month first.")
            return

        bid = self.app.business_id
        year = self.app.year
        month = self.current_month

        # Read and validate inputs
        try:
            price = float(self.entries["Price change (%)"].get().strip())
            marketing = float(self.entries["Marketing spend (RM)"].get().strip())
            staff_adj = float(self.entries["Staff cost adjustment (RM)"].get().strip())
            waste = float(self.entries["Waste reduction (%)"].get().strip())
            inv = float(self.entries["Inventory tightness (0–1)"].get().strip())
        except ValueError:
            messagebox.showerror(
                "Invalid input", "Please make sure all fields are numbers."
            )
            return

        # Validation rules
        if not (1 <= month <= 12):
            messagebox.showerror("Invalid month", "Month must be between 1 and 12.")
            return
        if marketing < 0:
            messagebox.showerror(
                "Invalid marketing spend", "Marketing spend must be 0 or more."
            )
            return
        if not (-100 <= price <= 100):
            messagebox.showerror(
                "Invalid price change",
                "Price change (%) should be between -100 and 100.",
            )
            return
        if not (0 <= waste <= 100):
            messagebox.showerror(
                "Invalid waste reduction",
                "Waste reduction (%) must be between 0 and 100.",
            )
            return
        if not (0 <= inv <= 1):
            messagebox.showerror(
                "Invalid inventory tightness",
                "Inventory tightness must be between 0 and 1.",
            )
            return

        row = [
            str(bid),
            str(year),
            str(month),
            f"{price:.6f}",
            f"{marketing:.2f}",
            f"{staff_adj:.2f}",
            f"{waste:.6f}",
            f"{inv:.6f}",
            "HUMAN",
        ]

        save_decision(row, year)


        self.decisions_by_month[month] = row
        idx = month - 1
        self.months.delete(idx)
        self.months.insert(idx, f"Month {month:02d}  ✅")

        self.status.config(text=f"✅ Saved Month {month} decision successfully.")
        messagebox.showinfo("Saved", f"Month {month} decision saved successfully.")


class SetSurvivalGoalPage(BasePage):
    """
    Option 3 GUI:
    - Show monthly cash/profit table
    - Calculate actual runway based on recent losses
    - Set runway goal 
    - Optional what-if calculator
    """

    def __init__(self, app):
        super().__init__(app)
        self.results = None
        self.actual_runway = None
        self.current_goal = None

        top = tk.Frame(self.frame, bg=THEME["bg"])
        top.pack(fill="x", padx=24, pady=18)

        tk.Label(
            top,
            text="Set Survival Goal (Cash Runway)",
            bg=THEME["bg"],
            fg=THEME["text"],
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")

        tk.Button(
            top,
            text="Back",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=14,
            pady=8,
            command=lambda: self.app.show("MenuPage"),
        ).pack(side="right")

        panel = tk.Frame(
            self.frame,
            bg=THEME["panel"],
            highlightthickness=1,
            highlightbackground="#22313F",
        )
        panel.pack(fill="both", expand=True, padx=24, pady=12)

        intro = (
            "Cash runway = how many months your business can survive if losses continue.\n"
            "Example: Losing RM5,000/month with RM30,000 cash → runway ≈ 6 months.\n\n"
            "This page uses your saved simulation results. If you see 'No results', run Full Business Analysis first."
        )

        self.status = tk.Label(
            panel,
            text=intro,
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 11),
            justify="left",
            wraplength=980,
        )
        self.status.pack(anchor="nw", padx=18, pady=(18, 12))

        body = tk.Frame(panel, bg=THEME["panel"])
        body.pack(fill="both", expand=True, padx=18, pady=18)

        # ---------------- Left: Results table ----------------
        left = tk.Frame(body, bg=THEME["panel"])
        left.pack(side="left", fill="both", expand=True)

        tk.Label(
            left,
            text="Recent Monthly Performance",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        table_frame = tk.Frame(left, bg=THEME["panel"])
        table_frame.pack(fill="both", expand=True)

        self.table = tk.Listbox(table_frame, height=16)
        self.table.pack(fill="both", expand=True)

        # ---------------- Right: Goal + What-if ----------------
        right = tk.Frame(body, bg=THEME["panel"])
        right.pack(side="left", fill="y", padx=(18, 0))

        # Goal section
        tk.Label(
            right,
            text="Runway Goal",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        tk.Label(
            right,
            text="Goal (months)",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 11),
        ).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=8)
        self.goal_entry = tk.Entry(right, width=18)
        self.goal_entry.grid(row=1, column=1, sticky="w", pady=8)
        ToolTip(
            self.goal_entry,
            "Enter how many months of runway you want. Example: 6 or 12",
        )

        self.goal_hint = tk.Label(
            right,
            text="",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 10),
            justify="left",
            wraplength=330,
        )
        self.goal_hint.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Button(
            right,
            text="Save Goal",
            bg=THEME["accent"],
            fg="black",
            relief="flat",
            padx=14,
            pady=8,
            command=self.save_goal,
        ).grid(row=3, column=0, sticky="w", pady=(0, 10))

        tk.Button(
            right,
            text="Recalculate",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=14,
            pady=8,
            command=self.recalculate,
        ).grid(row=3, column=1, sticky="w", pady=(0, 10))

        # Progress bar
        tk.Label(
            right,
            text="Progress",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(14, 8))

        self.progress_canvas = tk.Canvas(
            right, width=320, height=28, bg=THEME["panel"], highlightthickness=0
        )
        self.progress_canvas.grid(row=5, column=0, columnspan=2, sticky="w")

        self.progress_text = tk.Label(
            right,
            text="",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 11),
            justify="left",
            wraplength=330,
        )
        self.progress_text.grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.risk_text = tk.Label(
            right,
            text="",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 11),
            justify="left",
            wraplength=330,
        )
        self.risk_text.grid(row=7, column=0, columnspan=2, sticky="w", pady=(8, 0))


        # What-if section
        tk.Label(
            right,
            text="What-if Simulator",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).grid(row=8, column=0, columnspan=2, sticky="w", pady=(18, 8))

        tk.Label(
            right,
            text="Projected cash (RM)",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 11),
        ).grid(row=9, column=0, sticky="w", padx=(0, 10), pady=8)
        self.what_cash = tk.Entry(right, width=18)
        self.what_cash.grid(row=9, column=1, sticky="w", pady=8)
        ToolTip(self.what_cash, "Example: 30000 (your planned cash amount)")

        tk.Label(
            right,
            text="Projected monthly loss (RM)",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 11),
        ).grid(row=10, column=0, sticky="w", padx=(0, 10), pady=8)
        self.what_loss = tk.Entry(right, width=18)
        self.what_loss.grid(row=10, column=1, sticky="w", pady=8)
        ToolTip(self.what_loss, "Example: 5000 (loss per month). Must be > 0.")

        tk.Button(
            right,
            text="Simulate",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=14,
            pady=8,
            command=self.simulate,
        ).grid(row=11, column=0, sticky="w", pady=(8, 0))

        self.sim_text = tk.Label(
            right,
            text="",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 11),
            justify="left",
            wraplength=330,
        )
        self.sim_text.grid(row=12, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def on_show(self):
        self.load_and_display()

    # ---------- Core logic ----------
    def load_and_display(self):
        bid, year = self.app.business_id, self.app.year
        self.results = load_results(bid, year)

        self.table.delete(0, tk.END)

        if not self.results:
            self.status.config(
                text="⚠ No simulation results found yet. Run 'Full Business Analysis' first."
            )
            self._draw_progress(None, None)
            self.progress_text.config(text="")
            self.risk_text.config(text="")
            self.goal_hint.config(text="")
            self.sim_text.config(text="")
            return

        # Display table
        self.status.config(
            text="Below are your monthly results. This goal tracks how long your cash can last."
        )
        self.table.insert(tk.END, "Month | Cash End (RM) | Profit/Loss (RM)")
        self.table.insert(tk.END, "-" * 40)

        profits = []
        cash_ends = []

        for idx, r in enumerate(self.results, start=1):
            try:
                profit = float(r[7])
                cash_end = float(r[8])
            except:
                continue
            profits.append(profit)
            cash_ends.append(cash_end)
            self.table.insert(
                tk.END, f"{idx:>5} | {cash_end:>12,.2f} | {profit:>14,.2f}"
            )

        # Compute actual runway (same spirit as your CLI logic)
        cash_now = cash_ends[-1] if cash_ends else 0.0
        loss_months = [abs(p) for p in profits if p < 0]

        if not loss_months:
            self.actual_runway = float("inf")
        else:
            recent_losses = loss_months[-3:] if len(loss_months) >= 3 else loss_months
            avg_loss = sum(recent_losses) / len(recent_losses)
            self.actual_runway = (cash_now / avg_loss) if avg_loss > 0 else float("inf")

        # Load existing goal (if any)
        self.current_goal = get_goal(bid)
        if self.current_goal is not None:
            self.goal_entry.delete(0, tk.END)
            self.goal_entry.insert(0, str(self.current_goal))
            self.goal_hint.config(
                text=f"Saved goal found: {self.current_goal:.1f} months"
            )
        else:
            self.goal_hint.config(
                text="No saved goal yet. Enter a goal and click Save Goal."
            )

        # Show progress if goal exists
        if self.current_goal is not None and self.current_goal > 0:
            self._render_status(self.actual_runway, self.current_goal)
        else:
            self._draw_progress(None, None)
            self.progress_text.config(
                text=f"Actual runway: {self._fmt_runway(self.actual_runway)} months"
            )
            self.risk_text.config(text="Set a goal to see progress and safety status.")

        self.sim_text.config(text="")

    def recalculate(self):
        # Re-run computations + refresh view
        self.load_and_display()

    def save_goal(self):
        bid = self.app.business_id
        raw = self.goal_entry.get().strip()
        try:
            goal = float(raw)
            if goal <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror(
                "Invalid Goal", "Runway goal must be a positive number (e.g., 6 or 12)."
            )
            return

        set_goal(bid, goal)
        self.current_goal = goal
        self.goal_hint.config(text=f"✅ Goal saved: {goal:.1f} months")
        self._render_status(self.actual_runway, self.current_goal)
        messagebox.showinfo(
            "Saved", f"Runway goal saved for business {bid}: {goal:.1f} months"
        )

    def simulate(self):
        # What-if: projected runway = new_cash / new_loss
        try:
            new_cash = float(self.what_cash.get().strip())
            new_loss = float(self.what_loss.get().strip())
            if new_loss <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror(
                "Invalid Input", "Enter valid numbers.\nMonthly loss must be > 0."
            )
            return

        projected = (new_cash / new_loss) if new_loss > 0 else float("inf")

        if self.current_goal is not None and self.current_goal > 0:
            ratio = min(projected / self.current_goal, 1.0)
            self.sim_text.config(
                text=(
                    f"Projected runway: {self._fmt_runway(projected)} months\n"
                    f"Progress vs goal: {ratio*100:.1f}%"
                )
            )
        else:
            self.sim_text.config(
                text=f"Projected runway: {self._fmt_runway(projected)} months\n(Set a goal to compare.)"
            )

    # ---------- UI rendering helpers ----------
    def _fmt_runway(self, r):
        if r == float("inf"):
            return "Unlimited"
        if r >= 24:
            return "24+"
        return f"{r:.1f}"

    def _render_status(self, actual, goal):
        self._draw_progress(actual, goal)

        actual_str = self._fmt_runway(actual)
        self.progress_text.config(
            text=f"Target runway: {goal:.1f} months\nActual runway: {actual_str} months"
        )

        # Status text similar to your CLI logic but GUI-friendly
        if actual == float("inf") or actual >= goal:
            self.risk_text.config(
                fg=THEME["text"],
                text="✅ SAFE — Strong cash buffer.\nTip: Consider growth experiments or marketing tests.",
            )
        elif actual >= 0.5 * goal:
            short = goal - (actual if actual != float("inf") else goal)
            self.risk_text.config(
                fg=THEME["text"],
                text=f"⚠ AT RISK — Short by ~{short:.1f} months.\nTip: Focus on sales or reduce monthly losses.",
            )
        else:
            short = goal - (actual if actual != float("inf") else goal)
            self.risk_text.config(
                fg=THEME["text"],
                text=f"🚨 DANGER — Short by ~{short:.1f} months.\nTip: Cut costs and improve cashflow urgently.",
            )

    def _draw_progress(self, actual, goal):
        """
        Draw a simple progress bar on a Canvas.
        """
        c = self.progress_canvas
        c.delete("all")

        # Bar background
        x0, y0, x1, y1 = 0, 0, 320, 28
        c.create_rectangle(x0, y0, x1, y1, fill="#22313F", outline="#22313F")

        if actual is None or goal is None or goal <= 0:
            # show empty
            c.create_rectangle(
                x0, y0, x0, y1, fill=THEME["accent"], outline=THEME["accent"]
            )
            c.create_text(
                160, 14, text="No goal set", fill=THEME["muted"], font=("Segoe UI", 10)
            )
            return

        # compute fill ratio
        if actual == float("inf"):
            ratio = 1.0
        else:
            ratio = min(actual / goal, 1.0)

        fill_w = int(320 * ratio)
        c.create_rectangle(
            x0, y0, fill_w, y1, fill=THEME["accent"], outline=THEME["accent"]
        )
        c.create_text(
            160,
            14,
            text=f"{ratio*100:.1f}%",
            fill="black",
            font=("Segoe UI", 10, "bold"),
        )


class ReviewPastRunsPage(BasePage):
    """
    Option 4 GUI:
    - Load run history for business
    - Show runs newest-first
    - Select a run to view details
    - Highlight best/worst total_profit
    """

    def __init__(self, app):
        super().__init__(app)
        self.history = []
        self.best = None
        self.worst = None

        top = tk.Frame(self.frame, bg=THEME["bg"])
        top.pack(fill="x", padx=24, pady=18)

        tk.Label(
            top,
            text="Review Past Runs (History Comparison)",
            bg=THEME["bg"],
            fg=THEME["text"],
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")

        tk.Button(
            top,
            text="Back",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=14,
            pady=8,
            command=lambda: self.app.show("MenuPage"),
        ).pack(side="right")

        panel = tk.Frame(
            self.frame,
            bg=THEME["panel"],
            highlightthickness=1,
            highlightbackground="#22313F",
        )
        panel.pack(fill="both", expand=True, padx=24, pady=12)

        self.status = tk.Label(
            panel,
            text="This page compares your past simulation runs. Select a run to see details.",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 11),
            justify="left",
            wraplength=980,
        )
        self.status.pack(anchor="nw", padx=18, pady=(18, 10))

        body = tk.Frame(panel, bg=THEME["panel"])
        body.pack(fill="both", expand=True, padx=18, pady=18)

        # Left: run list
        left = tk.Frame(body, bg=THEME["panel"])
        left.pack(side="left", fill="y")

        tk.Label(
            left,
            text="Saved Runs",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        self.runs = tk.Listbox(left, width=42, height=18)
        self.runs.pack(fill="y")
        self.runs.bind("<<ListboxSelect>>", self.on_select_run)

        # Right: details
        right = tk.Frame(body, bg=THEME["panel"])
        right.pack(side="left", fill="both", expand=True, padx=(18, 0))

        tk.Label(
            right,
            text="Run Details",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")

        self.detail = tk.Label(
            right,
            text="Select a run on the left.",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12),
            justify="left",
            wraplength=650,
        )
        self.detail.pack(anchor="nw", pady=(10, 0))

        # Bottom: summary insights
        bottom = tk.Frame(panel, bg=THEME["panel"])
        bottom.pack(fill="x", padx=18, pady=(0, 18))

        tk.Label(
            bottom,
            text="Summary Insights",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(10, 6))

        self.summary = tk.Label(
            bottom,
            text="",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 11),
            justify="left",
            wraplength=980,
        )
        self.summary.pack(anchor="w")

    def on_show(self):
        self.load_history_into_ui()

    def load_history_into_ui(self):
        bid = self.app.business_id
        self.history = load_history(bid)

        self.runs.delete(0, tk.END)
        self.detail.config(text="Select a run on the left.")
        self.summary.config(text="")
        self.best = None
        self.worst = None

        if not self.history:
            self.status.config(text="⚠ No past simulation runs found.\nRun 'Full Business Analysis' first to generate history.")
            return

        self.history = sorted(self.history, key=lambda h: h.get("run_datetime", ""), reverse=True)
        # Compute best/worst by total_profit
        for i, h in enumerate(self.history, start=1):
            try:
                total_profit = float(h.get("total_profit", 0))
            except:
                total_profit = 0.0

            if self.best is None or total_profit > self.best["profit"]:
                self.best = {"idx": i, "profit": total_profit, "h": h}
            if self.worst is None or total_profit < self.worst["profit"]:
                self.worst = {"idx": i, "profit": total_profit, "h": h}

        # Populate listbox
        for idx, h in enumerate(self.history, start=1):
            date = h.get("date", "Unknown date")
            health = h.get("health_mostly", "N/A")
            try:
                profit = float(h.get("total_profit", 0))
            except:
                profit = 0.0

            tag = ""
            if self.best and idx == self.best["idx"]:
                tag = " 🏆 BEST"
            elif self.worst and idx == self.worst["idx"]:
                tag = " ⚠ WORST"

            self.runs.insert(
                tk.END, f"Run {idx:02d} | {date} | {health} | RM{profit:,.0f}{tag}"
            )

        # Show summary insights
        if self.best and self.worst:
            self.summary.config(
                text=(
                    f"Best run  : Run {self.best['idx']:02d} (RM{self.best['profit']:,.0f})\n"
                    f"Worst run : Run {self.worst['idx']:02d} (RM{self.worst['profit']:,.0f})\n"
                    f"Tip: Compare what decisions or conditions may have led to better runway and profit."
                )
            )

        self.status.config(
            text="Select a run to view details. Best/Worst are tagged for quick comparison."
        )

    def on_select_run(self, _=None):
        sel = self.runs.curselection()
        if not sel:
            return
        idx = sel[0]  # 0-based list index
        if idx >= len(self.history):
            return

        h = self.history[idx]

        # Parse numeric values safely
        def to_float(x, default=0.0):
            try:
                return float(x)
            except:
                return default

        total_profit = to_float(h.get("total_profit", 0))
        ending_cash = to_float(h.get("ending_cash", 0))

        min_runway_raw = h.get("min_runway", "")
        min_runway = None
        if isinstance(min_runway_raw, str) and min_runway_raw.lower() == "stable":
            min_runway = None
        else:
            try:
                min_runway = float(min_runway_raw)
            except:
                min_runway = None

        # Risk label (same idea as CLI)
        if min_runway is None:
            risk = "Low (Stable / Not Losing Money)"
        else:
            risk = (
                "Low" if min_runway >= 6 else "Moderate" if min_runway >= 3 else "High"
            )

        notes = h.get("notes", "")

        # Badge text
        badge = ""
        if self.best and (idx + 1) == self.best["idx"]:
            badge = "🏆 BEST RUN"
        elif self.worst and (idx + 1) == self.worst["idx"]:
            badge = "⚠ WORST RUN"

        # Build detail text
        detail_text = (
            f"{badge}\n\n"
            f"Date        : {h.get('date', 'N/A')}\n"
            f"Run time    : {h.get('run_datetime', 'N/A')}\n\n"
            f"Total Profit: RM{total_profit:,.0f}\n"
            f"Final Cash  : RM{ending_cash:,.0f}\n"
            f"Min Runway  : {min_runway_raw}\n"
            f"Health      : {h.get('health_mostly', 'N/A')}\n"
            f"Risk Level  : {risk}\n"
        )

        if notes:
            detail_text += f"\nNotes:\n{notes}\n"

        detail_text += "\nSuggested reflection:\n- What changed in decisions (price, marketing, staff, waste, inventory)?\n- Did runway improve compared to other runs?\n- Is the result repeatable or risky?"

        self.detail.config(text=detail_text)


class SensitivityTestPage(BasePage):
    """
    Option 5 GUI:
    - Loads company + decisions
    - Runs run_sensitivity(...) for a representative month (Month 1)
    - Displays ranked levers and impacts
    """

    def __init__(self, app):
        super().__init__(app)
        self.results = []

        top = tk.Frame(self.frame, bg=THEME["bg"])
        top.pack(fill="x", padx=24, pady=18)

        tk.Label(
            top,
            text="Sensitivity Test (What Matters Most?)",
            bg=THEME["bg"],
            fg=THEME["text"],
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")

        tk.Button(
            top,
            text="Back",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=14,
            pady=8,
            command=lambda: self.app.show("MenuPage"),
        ).pack(side="right")

        panel = tk.Frame(
            self.frame,
            bg=THEME["panel"],
            highlightthickness=1,
            highlightbackground="#22313F",
        )
        panel.pack(fill="both", expand=True, padx=24, pady=12)

        intro = (
            "Sensitivity analysis shows which decision lever changes profit the MOST\n"
            "when adjusted slightly. This helps you focus on the highest-impact action first.\n\n"
            "Example: If changing 'Pricing' slightly improves profit more than 'Marketing',\n"
            "then pricing is your best first lever to work on."
        )

        self.status = tk.Label(
            panel,
            text=intro,
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 11),
            justify="left",
            wraplength=980,
        )
        self.status.pack(anchor="nw", padx=18, pady=(18, 10))

        btn_row = tk.Frame(panel, bg=THEME["panel"])
        btn_row.pack(anchor="nw", padx=18, pady=(0, 12))

        tk.Button(
            btn_row,
            text="Run Sensitivity Test",
            bg=THEME["accent"],
            fg="black",
            relief="flat",
            padx=16,
            pady=10,
            command=self.run_test,
        ).pack(side="left")

        tk.Button(
            btn_row,
            text="Clear",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=16,
            pady=10,
            command=self.clear,
        ).pack(side="left", padx=10)

        body = tk.Frame(panel, bg=THEME["panel"])
        body.pack(fill="both", expand=True, padx=18, pady=18)

        # Left: ranked list
        left = tk.Frame(body, bg=THEME["panel"])
        left.pack(side="left", fill="y")

        tk.Label(
            left,
            text="Ranked Levers",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        self.listbox = tk.Listbox(left, width=46, height=18)
        self.listbox.pack(fill="y")
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        # Right: explanation
        right = tk.Frame(body, bg=THEME["panel"])
        right.pack(side="left", fill="both", expand=True, padx=(18, 0))

        tk.Label(
            right,
            text="What this means",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")

        self.detail = tk.Label(
            right,
            text="Run the test to see which lever has the biggest effect.",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12),
            justify="left",
            wraplength=650,
        )
        self.detail.pack(anchor="nw", pady=(10, 0))

        self.biggest = tk.Label(
            right,
            text="",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 11, "bold"),
            justify="left",
            wraplength=650,
        )
        self.biggest.pack(anchor="nw", pady=(16, 0))

    def on_show(self):
        self.clear()

    def clear(self):
        self.results = []
        self.listbox.delete(0, tk.END)
        self.detail.config(
            text="Run the test to see which lever has the biggest effect."
        )
        self.biggest.config(text="")
        self.status.config(
            text=(
                "Sensitivity analysis shows which decision lever changes profit the MOST\n"
                "when adjusted slightly. This helps you focus on the highest-impact action first.\n\n"
                "Click 'Run Sensitivity Test' to begin."
            )
        )

    def run_test(self):
        bid, year = self.app.business_id, self.app.year

        self.status.config(text="Running sensitivity test… (please wait)")
        self.listbox.delete(0, tk.END)
        self.detail.config(text="")
        self.biggest.config(text="")

        def worker():
            try:
                # Load company
                company_row = load_company(bid)
                if not company_row:
                    raise ValueError(
                        "Company not found. Please ensure company.csv has this business_id."
                    )

                company = company_row_to_object(company_row)

                # Load decisions
                decision_rows = load_decisions(bid, year)
                if not decision_rows:
                    raise ValueError(
                        "No decisions found for this year. Please fill decisions CSV first."
                    )

                decisions = decision_rows_to_objects(decision_rows, year, allow_save=False)

                # Use Month 1 as baseline (same as your CLI sensitivity test)
                base_decision = decisions[0]
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

                self.results = sensitivity_results or []

                self.frame.after(0, self._render_results)

            except Exception as e:
                self.frame.after(
                    0, lambda: messagebox.showerror("Sensitivity Test Error", str(e))
                )
                self.frame.after(
                    0, lambda: self.status.config(text="⚠ Sensitivity test failed.")
                )

        threading.Thread(target=worker, daemon=True).start()

    def _render_results(self):
        if not self.results:
            self.status.config(text="⚠ No sensitivity results available.")
            return

        self.status.config(text="Done. Click a lever to see explanation.")
        self.listbox.delete(0, tk.END)

        # Results are usually sorted best-first already
        for idx, r in enumerate(self.results, start=1):
            lever = r.get("lever", "Unknown")
            impact = float(r.get("profit_change", 0))
            arrow = "↑" if impact > 0 else "↓"
            self.listbox.insert(
                tk.END, f"{idx:02d}. {lever:<22} {arrow} RM{abs(impact):,.0f}/month"
            )

        biggest = self.results[0].get("lever", "Unknown")
        self.biggest.config(
            text=(
                f"📌 Most impactful lever: {biggest}\n"
                "Tip: Start improving this lever first — small changes here usually give the biggest payoff."
            )
        )

        # Auto-select first item
        self.listbox.selection_set(0)
        self.on_select()

    def on_select(self, _=None):
        if not self.results:
            return
        sel = self.listbox.curselection()
        if not sel:
            return
        r = self.results[sel[0]]

        lever = r.get("lever", "Unknown")
        impact = float(r.get("profit_change", 0))
        arrow = "increase" if impact > 0 else "decrease"

        explanation = (
            f"Lever: {lever}\n\n"
            f"Estimated effect: RM{abs(impact):,.0f}/month ({'positive' if impact > 0 else 'negative'} change)\n\n"
            f"How to use this:\n"
            f"- Try a small {arrow} adjustment in '{lever}'\n"
            f"- Re-run Full Business Analysis to confirm impact across the year\n"
            f"- Focus on 1–2 top levers instead of changing everything at once"
        )

        self.detail.config(text=explanation)


class IntelligentAdvisorPage(BasePage):
    """
    Option 6 GUI:
    - Runs GeneticOptimizer.optimize_with_logs(...) in background thread
    - Shows live GA progress (generation -> fitness)
    - Displays best decisions by month
    - Saves best decisions to decisions_{year}.csv using save_decision(...)
    """

    def __init__(self, app):
        super().__init__(app)

        self.best_decisions = None
        self.best_fitness = None
        self.ga_logs = None
        self._worker_running = False

        top = tk.Frame(self.frame, bg=THEME["bg"])
        top.pack(fill="x", padx=24, pady=18)

        tk.Label(
            top,
            text="Intelligent Advisor (AI Optimizer)",
            bg=THEME["bg"],
            fg=THEME["text"],
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")

        tk.Button(
            top,
            text="Back",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=14,
            pady=8,
            command=lambda: (
                self.app.show("MenuPage")
                if not self._worker_running
                else messagebox.showwarning(
                    "Running",
                    "Optimizer is still running. Please wait for it to finish.",
                )
            ),
        ).pack(side="right")

        panel = tk.Frame(
            self.frame,
            bg=THEME["panel"],
            highlightthickness=1,
            highlightbackground="#22313F",
        )
        panel.pack(fill="both", expand=True, padx=24, pady=12)

        intro = (
            "The Intelligent Advisor uses a Genetic Algorithm (GA) to search many strategies.\n"
            "It tries different monthly decisions, simulates 12 months, then keeps improving.\n\n"
            "Fitness score combines:\n"
            "• Total yearly profit (higher is better)\n"
            "• Worst cash runway month (safer cashflow is better)\n"
            "• Bankruptcy penalty\n"
        )

        self.status = tk.Label(
            panel,
            text=intro,
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 11),
            justify="left",
            wraplength=980,
        )
        self.status.pack(anchor="nw", padx=18, pady=(18, 10))

        # Buttons row
        btn_row = tk.Frame(panel, bg=THEME["panel"])
        btn_row.pack(anchor="nw", padx=18, pady=(0, 12))

        self.run_btn = tk.Button(
            btn_row,
            text="Run AI Optimizer",
            bg=THEME["accent"],
            fg="black",
            relief="flat",
            padx=16,
            pady=10,
            command=self.run_optimizer,
        )
        self.run_btn.pack(side="left")

        self.save_btn = tk.Button(
            btn_row,
            text="Save AI Decisions",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=16,
            pady=10,
            command=self.save_ai_decisions,
            state="disabled",
        )
        self.save_btn.pack(side="left", padx=10)

        tk.Button(
            btn_row,
            text="Clear",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=16,
            pady=10,
            command=self.clear,
        ).pack(side="left")

        # Body split: left progress logs, right best decisions
        body = tk.Frame(panel, bg=THEME["panel"])
        body.pack(fill="both", expand=True, padx=18, pady=18)

        # Left: GA progress
        left = tk.Frame(body, bg=THEME["panel"])
        left.pack(side="left", fill="y")

        tk.Label(
            left,
            text="GA Progress (Fitness by Generation)",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        self.log_list = tk.Listbox(left, width=48, height=20)
        self.log_list.pack(fill="y")

        self.progress_canvas = tk.Canvas(
            left, width=360, height=24, bg=THEME["panel"], highlightthickness=0
        )
        self.progress_canvas.pack(anchor="w", pady=(12, 0))

        self.progress_label = tk.Label(
            left,
            text="",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 10),
            justify="left",
            wraplength=360,
        )
        self.progress_label.pack(anchor="w", pady=(8, 0))

        # Right: Best results
        right = tk.Frame(body, bg=THEME["panel"])
        right.pack(side="left", fill="both", expand=True, padx=(18, 0))

        tk.Label(
            right,
            text="Best AI Plan (Monthly Decisions)",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")

        self.best_summary = tk.Label(
            right,
            text="Run the optimizer to generate AI decisions.",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12),
            justify="left",
            wraplength=620,
        )
        self.best_summary.pack(anchor="nw", pady=(10, 10))

        self.plan_list = tk.Listbox(right, height=18)
        self.plan_list.pack(fill="both", expand=True)

    def on_show(self):
        # keep whatever already displayed; don’t clear automatically
        pass

    def clear(self):
        if self._worker_running:
            messagebox.showwarning(
                "Running", "Optimizer is still running. Please wait."
            )
            return
        self.best_decisions = None
        self.best_fitness = None
        self.ga_logs = None
        self.log_list.delete(0, tk.END)
        self.plan_list.delete(0, tk.END)
        self.best_summary.config(text="Run the optimizer to generate AI decisions.")
        self.save_btn.config(state="disabled")
        self._draw_progress(0.0)
        self.progress_label.config(text="")

    def run_optimizer(self):
        if self._worker_running:
            messagebox.showinfo("Running", "Optimizer is already running.")
            return

        bid, year = self.app.business_id, self.app.year
        self.clear()

        # Validate company exists
        company_row = load_company(bid)
        if not company_row:
            messagebox.showerror(
                "Missing Company",
                "Company not found. Please ensure company.csv has this business_id.",
            )
            return

        company = company_row_to_object(company_row)
        market = create_default_market(company.business_type)
        simulator = BusinessSimulator(seed=42)

        self._worker_running = True
        self.run_btn.config(state="disabled")
        self.status.config(
            text="AI Optimizer is running… This may take some time.\nYou can watch fitness improve by generation."
        )
        self.progress_label.config(text="Starting…")
        self._draw_progress(0.02)

        def worker():
            try:
                optimizer = GeneticOptimizer()

                # Your optimizer returns: best_decisions, best_fitness, ga_logs
                best_decisions, best_fitness, ga_logs = optimizer.optimize_with_logs(
                    company, market, simulator, bid, year
                )

                self.best_decisions = best_decisions
                self.best_fitness = best_fitness
                self.ga_logs = ga_logs or []

                self.frame.after(0, self._render_done)

            except Exception as e:
                self.frame.after(
                    0, lambda: messagebox.showerror("Optimizer Error", str(e))
                )
                self.frame.after(0, self._finish_fail)

        threading.Thread(target=worker, daemon=True).start()

        # UI updater loop while running (shows partial progress if logs grow)
        self._poll_progress()

    def _poll_progress(self):
        """
        Poll the GA logs list if optimizer appends logs progressively.
        Even if logs only appear at the end, this still works safely.
        """
        if not self._worker_running:
            return

        # If ga_logs is being filled progressively, show latest snapshot.
        if isinstance(self.ga_logs, list) and self.ga_logs:
            self._render_logs_live()

        # keep polling
        self.frame.after(600, self._poll_progress)

    def _render_logs_live(self):
        # Repaint listbox with current logs (avoid duplicates)
        self.log_list.delete(0, tk.END)
        logs = self.ga_logs or []
        if not logs:
            return

        max_fit = max(f for _, f in logs) if logs else 1.0
        last_gen, last_fit = logs[-1]
        ratio = (last_fit / max_fit) if max_fit > 0 else 0.0

        for gen, fit in logs[-80:]:  # keep UI light
            self.log_list.insert(
                tk.END, f"Gen {int(gen):>3}  Fitness: {float(fit):,.2f}"
            )

        self._draw_progress(min(max(ratio, 0.02), 1.0))
        self.progress_label.config(
            text=f"Latest: Gen {int(last_gen)} | Fitness {float(last_fit):,.2f}"
        )

    def _render_done(self):
        self._worker_running = False
        self.run_btn.config(state="normal")

        logs = self.ga_logs or []
        self.log_list.delete(0, tk.END)

        if logs:
            for gen, fit in logs:
                self.log_list.insert(
                    tk.END, f"Gen {int(gen):>3}  Fitness: {float(fit):,.2f}"
                )

            max_fit = max(f for _, f in logs) if logs else 1.0
            last_gen, last_fit = logs[-1]
            ratio = (last_fit / max_fit) if max_fit > 0 else 1.0
            self._draw_progress(min(max(ratio, 0.05), 1.0))
            self.progress_label.config(
                text=f"Completed: {len(logs)} generations. Final fitness: {float(last_fit):,.2f}"
            )
        else:
            self._draw_progress(1.0)
            self.progress_label.config(
                text="Completed. (No logs returned by optimizer.)"
            )

        if not self.best_decisions:
            self.best_summary.config(
                text="No best decisions returned. Please check optimizer implementation."
            )
            return

        # Build summary + plan list
        self.plan_list.delete(0, tk.END)

        # Executive summary (similar to CLI but GUI-friendly)
        start_score = float(logs[0][1]) if logs else None
        final_score = (
            float(self.best_fitness) if self.best_fitness is not None else None
        )

        if start_score is not None and final_score is not None:
            improvement = final_score - start_score
            summary = (
                f"✅ Best fitness score: {final_score:,.2f}\n"
                f"Started at: {start_score:,.2f}  →  Improved by: +{improvement:,.2f}\n\n"
                "This plan aims to increase profit while reducing bankruptcy risk."
            )
        elif final_score is not None:
            summary = f"✅ Best fitness score: {final_score:,.2f}\n\nThis plan aims to increase profit while reducing bankruptcy risk."
        else:
            summary = "✅ AI plan generated.\n\nThis plan aims to increase profit while reducing bankruptcy risk."

        self.best_summary.config(text=summary)

        # Show decisions by month
        for d in self.best_decisions:
            action_summary = (
                f"Month {d.month:02d} | "
                f"Price {('+' if d.price_change_pct > 0 else '')}{d.price_change_pct*100:.1f}% | "
                f"Marketing RM{d.marketing_spend:,.0f} | "
                f"Staff {('+' if d.staff_cost_adjustment > 0 else '')}{d.staff_cost_adjustment:,.0f} | "
                f"Waste {d.waste_reduction_pct*100:.1f}% | "
                f"Inventory {d.inventory_tightness:.2f}"
            )
            self.plan_list.insert(tk.END, action_summary)

        # Enable saving
        self.save_btn.config(state="normal")

        self.status.config(
            text=(
                "AI Optimizer completed.\n"
                "You can now save the AI decisions, then run 'Full Business Analysis' to see the month-by-month outcomes."
            )
        )

    def _finish_fail(self):
        self._worker_running = False
        self.run_btn.config(state="normal")
        self._draw_progress(0.0)
        self.progress_label.config(text="Failed.")

    def save_ai_decisions(self):
        if not self.best_decisions:
            messagebox.showwarning(
                "No AI Plan", "No AI decisions available. Run the optimizer first."
            )
            return

        bid, year = self.app.business_id, self.app.year

        # Save each decision row using same format used in CLI controller
        try:
            for d in self.best_decisions:
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

            messagebox.showinfo(
                "Saved",
                f"✅ AI decisions saved to decisions_{year}.csv.\n\nNext: Run 'Full Business Analysis' to view results.",
            )
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def _draw_progress(self, ratio):
        """
        Draw progress bar on canvas. ratio in [0,1].
        """
        c = self.progress_canvas
        c.delete("all")
        ratio = max(0.0, min(1.0, float(ratio)))

        # background
        c.create_rectangle(0, 0, 360, 24, fill="#22313F", outline="#22313F")
        # fill
        w = int(360 * ratio)
        c.create_rectangle(0, 0, w, 24, fill=THEME["accent"], outline=THEME["accent"])
        c.create_text(
            180,
            12,
            text=f"{ratio*100:.0f}%",
            fill="black",
            font=("Segoe UI", 10, "bold"),
        )


class CompareRunsPage(BasePage):
    """
    Compare Human vs AI runs
    """

    def __init__(self, app):
        super().__init__(app)
        self.history = []

        # ================= HEADER =================
        top = tk.Frame(self.frame, bg=THEME["bg"])
        top.pack(fill="x", padx=24, pady=18)

        tk.Label(
            top,
            text="Run Comparison: Human vs AI",
            bg=THEME["bg"],
            fg=THEME["text"],
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")

        tk.Button(
            top,
            text="Back",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=14,
            pady=8,
            command=lambda: self.app.show("MenuPage"),
        ).pack(side="right")

        # ================= PANEL =================
        panel = tk.Frame(
            self.frame,
            bg=THEME["panel"],
            highlightthickness=1,
            highlightbackground="#22313F",
        )
        panel.pack(fill="both", expand=True, padx=24, pady=12)

        self.status = tk.Label(
            panel,
            text=(
                "This page shows a comparison between your Human decisions\n"
                "and AI-generated decisions.\n\n"
                "Suggested steps:\n"
                "1) Run Full Analysis (Human)\n"
                "2) Run Intelligent Advisor (AI)\n"
                "3) Run Full Analysis again (AI)\n"
                "4) Compare results here"
            ),
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 11),
            justify="left",
            wraplength=980,
        )
        self.status.pack(anchor="nw", padx=18, pady=(18, 12))

        body = tk.Frame(panel, bg=THEME["panel"])
        body.pack(fill="both", expand=True, padx=18, pady=18)

        # ================= LEFT =================
        left = tk.Frame(body, bg=THEME["panel"])
        left.pack(side="left", fill="y")

        tk.Label(
            left,
            text="Run Summary",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        self.run_list = tk.Listbox(left, width=60, height=10)
        self.run_list.pack(pady=(6, 12))

        tk.Button(
            left,
            text="Compare Runs",
            bg=THEME["accent"],
            fg="black",
            relief="flat",
            padx=18,
            pady=12,
            command=self.compare,
        ).pack(anchor="w")

        # ================= RIGHT =================
        right = tk.Frame(body, bg=THEME["panel"])
        right.pack(side="left", fill="both", expand=True, padx=(18, 0))

        tk.Label(
            right,
            text="Comparison Results",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")

        self.result = tk.Label(
            right,
            text="Run comparison will appear here.",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 12),
            justify="left",
            wraplength=650,
        )
        self.result.pack(anchor="nw", pady=(10, 0))

        self.reco = tk.Label(
            right,
            text="",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 11),
            justify="left",
            wraplength=650,
        )
        self.reco.pack(anchor="nw", pady=(16, 0))

    # ================= LIFECYCLE =================
    def on_show(self):
        self.load_history()

    def load_history(self):
        bid = self.app.business_id
        self.history = load_history(bid)

        self.run_list.delete(0, tk.END)
        self.result.config(text="Run comparison will appear here.")
        self.reco.config(text="")

        if not self.history:
            self.status.config(
                text="⚠ No runs found. Run Full Analysis first."
            )
            return

        # sort newest first
        self.history = sorted(
            self.history,
            key=lambda h: h.get("run_datetime", ""),
            reverse=True,
        )

        for idx, h in enumerate(self.history, start=1):
            label = (
                f"Run {idx:02d} | {h.get('date')} | "
                f"Source {h.get('decision_source', 'UNKNOWN')} | "
                f"Health {h.get('health_mostly')} | "
                f"Profit RM{self._to_float(h.get('total_profit')):,.0f} | "
                f"Cash RM{self._to_float(h.get('ending_cash')):,.0f}"
            )
            self.run_list.insert(tk.END, label)

        self.status.config(
            text="Comparison uses the latest Human run and the latest AI run."
        )

    def compare(self):
        if not self.history:
            messagebox.showwarning(
                "No runs",
                "No run history available."
            )
            return

        ai_runs = [h for h in self.history if h.get("decision_source") == "AI"]
        human_runs = [h for h in self.history if h.get("decision_source") == "HUMAN"]

        if not ai_runs or not human_runs:
            messagebox.showerror(
                "Missing Runs",
                "You need at least one Human run and one AI run."
            )
            return

        after = ai_runs[0]      
        before = human_runs[0]  

        b_profit = self._to_float(before.get("total_profit", 0))
        a_profit = self._to_float(after.get("total_profit", 0))

        b_cash = self._to_float(before.get("ending_cash", 0))
        a_cash = self._to_float(after.get("ending_cash", 0))

        b_runway = before.get("min_runway", "N/A")
        a_runway = after.get("min_runway", "N/A")

        d_profit = a_profit - b_profit
        d_cash = a_cash - b_cash

        # ---------- PROFIT BADGE ----------
        if b_profit == 0:
            badge_line = "⚪ Comparison unavailable (baseline profit = 0)"
        else:
            profit_change_pct = ((a_profit - b_profit) / abs(b_profit)) * 100
            if profit_change_pct > 3:
                badge_line = f"🟢 AI performed better (+{profit_change_pct:.1f}%)"
            elif profit_change_pct < -3:
                badge_line = f"🔴 AI performed worse ({profit_change_pct:.1f}%)"
            else:
                badge_line = f"🟡 Profit unchanged ({profit_change_pct:+.1f}%)"

        self.result.config(
            text=(
                "Human → AI Comparison\n\n"
                f"Total Profit:\n"
                f"  Human: RM{b_profit:,.0f}\n"
                f"  AI   : RM{a_profit:,.0f}\n"
                f"  Change: RM{d_profit:+,.0f}\n\n"
                f"Ending Cash:\n"
                f"  Human: RM{b_cash:,.0f}\n"
                f"  AI   : RM{a_cash:,.0f}\n"
                f"  Change: RM{d_cash:+,.0f}\n\n"
                f"Min Runway:\n"
                f"  Human: {b_runway}\n"
                f"  AI   : {a_runway}"
            )
        )

        reco_lines = [badge_line, ""]

        reco_lines.append(
            "✅ Profit improved with AI decisions."
            if d_profit > 0
            else "⚠ Profit did not improve with AI decisions."
        )

        reco_lines.append(
            "✅ Cash position improved."
            if d_cash > 0
            else "⚠ Cash position worsened."
        )

        reco_lines.append(
            "\nNext step:\n"
            "• If AI performed better, you may adopt AI decisions.\n"
            "• Otherwise, review and adjust your strategy."
        )

        self.reco.config(text="\n".join(reco_lines))

    # ================= UTIL =================
    def _to_float(self, x, default=0.0):
        try:
            return float(x)
        except:
            return default


class ExportPDFPage(BasePage):
    def __init__(self, app):
        super().__init__(app)

        panel = tk.Frame(self.frame, bg=THEME["panel"])
        panel.pack(fill="both", expand=True, padx=40, pady=40)

        tk.Label(
            panel,
            text="Export AI Strategy to PDF",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w", pady=(0, 20))

        self.status = tk.Label(
            panel,
            text="This will export the latest AI-optimized strategy to PDF.",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 12),
        )
        self.status.pack(anchor="w", pady=(0, 20))

        tk.Button(
            panel,
            text="Export PDF",
            bg=THEME["accent"],
            fg="black",
            relief="flat",
            padx=20,
            pady=12,
            command=self.export_pdf,
        ).pack(anchor="w")

        tk.Button(
            panel,
            text="Back",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=20,
            pady=12,
            command=lambda: self.app.show("MenuPage"),
        ).pack(anchor="w", pady=(10, 0))

        tk.Button(
            panel,
            text="View Last Report",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=20,
            pady=12,
            command=self.view_last_pdf,
        ).pack(anchor="w", pady=(10, 0))

    def export_pdf(self):
        print("Export PDF clicked")  

        bid = self.app.business_id
        year = self.app.year
        decisions = load_decisions(bid, year, source="AI")
        if not decisions:
            messagebox.showerror(
                "No AI Strategy",
                "No AI decisions found. Run Intelligent Advisor first.",
            )
            return

        history = load_history(bid)
        if not history:
            messagebox.showerror(
                "No History",
                "No simulation history found. Run Full Analysis first.",
            )
            return

        latest = history[-1]

        summary_metrics = {
            "total_profit": float(latest["total_profit"]),
            "ending_cash": float(latest["ending_cash"]),
            "min_runway": latest["min_runway"],
            "risk_level": latest["health_mostly"],
        }

        company_row = load_company(bid)
        company = company_row_to_object(company_row)

        filename = export_ai_strategy_to_pdf(
            company=company,
            best_decisions=decisions,
            best_fitness=latest.get("fitness", 0),
            summary_metrics=summary_metrics,
            year=year,
        )
        self.app.last_report_path = filename

        print("PDF filename:", filename)  

        messagebox.showinfo(
            "PDF Exported",
            f"PDF successfully created:\n\n{filename}",
        )

    def view_last_pdf(self):
        path = getattr(self.app, "last_report_path", None)

        if not path or not os.path.exists(path):
            messagebox.showinfo(
                "No Report Found",
                "No PDF report found yet.\nPlease export a report first.",
            )
            return

        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform.startswith("darwin"):
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open PDF:\n{e}")


class PlaceholderPage(BasePage):
    def __init__(self, app):
        super().__init__(app)

        top = tk.Frame(self.frame, bg=THEME["bg"])
        top.pack(fill="x", padx=24, pady=18)

        tk.Label(
            top,
            text="This option will be converted next",
            bg=THEME["bg"],
            fg=THEME["text"],
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")

        tk.Button(
            top,
            text="Back",
            bg="#22313F",
            fg=THEME["text"],
            relief="flat",
            padx=14,
            pady=8,
            command=lambda: self.app.show("MenuPage"),
        ).pack(side="right")

        panel = tk.Frame(
            self.frame,
            bg=THEME["panel"],
            highlightthickness=1,
            highlightbackground="#22313F",
        )
        panel.pack(fill="both", expand=True, padx=24, pady=12)

        tk.Label(
            panel,
            text=(
                "Menu flow is ready.\n\n"
                "Next, we will implement this option as a fully interactive GUI page "
                "(forms, tables, buttons) without dumping CLI output."
            ),
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Segoe UI", 12),
            justify="left",
            wraplength=900,
        ).pack(anchor="nw", padx=18, pady=18)
