"""
Intelligent Advisor module using a Genetic Algorithm.
Optimizes 12-month business decisions to maximize profit and minimize risk.
"""

import random
from business_helpers import company_row_to_object
from simulation import BusinessSimulator
from market import create_default_market
from decision import Decision
from data_io import load_company, save_decision

# SHARED DECISION RANGES
DECISION_RANGES = [
    (-0.2, 0.2),  # price_change_pct
    (0, 2000),  # marketing_spend
    (-500, 500),  # staff_cost_adjustment
    (0, 0.3),  # waste_reduction_pct
    (0.5, 1.0),  # inventory_tightness
]


# ---------------- Chromosome ----------------
class Chromosome:
    """
    Represents a full-year or partial-year strategy.
    Each month × number of decision variables = total genes.
    """

    def __init__(self, months=12, genes=None):
        self.months = months
        self.genes = []
        if genes is None:
            for _ in range(self.months):
                for low, high in DECISION_RANGES:
                    self.genes.append(random.uniform(low, high))
        else:
            self.genes = genes[:]
        self.fitness = None

    def to_decisions(self, business_id, year):
        """Convert genes into Decision objects for all months."""
        decisions = []
        for month in range(1, self.months + 1):
            i = (month - 1) * len(DECISION_RANGES)
            decisions.append(
                Decision(
                    business_id, year, month, *self.genes[i : i + len(DECISION_RANGES)]
                )
            )
        return decisions


# ---------------- Genetic Optimizer ----------------
class GeneticOptimizer:
    def __init__(
        self,
        months=12,
        population_size=80,
        generations=150,
        mutation_rate=0.03,
        elitism_count=5,
    ):
        self.months = months
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.elitism_count = elitism_count

    # ---------------- Optimization ----------------
    def optimize(
        self, company, market, simulator, business_id, year, starting_cash=100_000
    ):
        population = [Chromosome(self.months) for _ in range(self.population_size)]
        fitness_history = []

        for gen in range(self.generations):
            # FITNESS
            for chrom in population:
                decisions = chrom.to_decisions(business_id, year)
                results = simulator.simulate_months(
                    company, market, decisions, starting_cash
                )

                if not results:
                    chrom.fitness = -1_000_000
                    continue

                total_profit = sum(r[3] for r in results)
                runways = []
                for r in results:
                    profit = r[3]
                    cash_end = r[4]
                    if profit < 0:
                        runway = cash_end / (-profit) if cash_end > 0 else 0
                    else:
                        runway = len(results)
                    runways.append(runway)
                min_runway = min(runways)
                ending_cash = results[-1][4]
                bankruptcy_penalty = -100_000 if ending_cash <= 0 else 0

                chrom.fitness = (
                    (total_profit / len(results)) * 0.7
                    + min_runway * 100 * 0.2
                    + bankruptcy_penalty
                )

            # SELECTION & EVOLUTION
            population.sort(key=lambda c: c.fitness, reverse=True)
            fitness_history.append(population[0].fitness)

            new_population = population[: self.elitism_count]
            while len(new_population) < self.population_size:
                p1 = self.tournament_select(population)
                p2 = self.tournament_select(population)
                child_genes = self.crossover(p1.genes, p2.genes)
                self.mutate(child_genes)
                new_population.append(Chromosome(self.months, child_genes))

            population = new_population
            print(
                f"Gen {gen+1:3}/{self.generations} | Best Fitness: {population[0].fitness:,.2f}"
            )

        self.visualize_evolution(fitness_history)
        best = population[0]
        return best.to_decisions(business_id, year), best.fitness

    # ---------------- Optimization with logs ----------------
    def optimize_with_logs(
        self, company, market, simulator, business_id, year, starting_cash=100_000
    ):
        population = [Chromosome(self.months) for _ in range(self.population_size)]
        ga_logs = []

        for gen in range(self.generations):
            for chrom in population:
                decisions = chrom.to_decisions(business_id, year)
                results = simulator.simulate_months(
                    company, market, decisions, starting_cash
                )

                if not results:
                    chrom.fitness = -1_000_000
                    continue

                total_profit = sum(r[3] for r in results)
                runways = []
                for r in results:
                    profit = r[3]
                    cash_end = r[4]
                    if profit < 0:
                        runway = cash_end / (-profit) if cash_end > 0 else 0
                    else:
                        runway = len(results)
                    runways.append(runway)
                min_runway = min(runways)
                ending_cash = results[-1][4]
                bankruptcy_penalty = -100_000 if ending_cash <= 0 else 0

                chrom.fitness = (
                    (total_profit / len(results)) * 0.7
                    + min_runway * 100 * 0.2
                    + bankruptcy_penalty
                )

            population.sort(key=lambda c: c.fitness, reverse=True)
            best_fitness = population[0].fitness
            ga_logs.append((gen + 1, best_fitness))
            print(
                f"Gen {gen+1:3}/{self.generations} | Best Fitness: {best_fitness:,.2f}"
            )

            new_population = population[: self.elitism_count]
            while len(new_population) < self.population_size:
                p1 = self.tournament_select(population)
                p2 = self.tournament_select(population)
                child_genes = self.crossover(p1.genes, p2.genes)
                self.mutate(child_genes)
                new_population.append(Chromosome(self.months, child_genes))

            population = new_population

        best_chrom = population[0]
        return best_chrom.to_decisions(business_id, year), best_chrom.fitness, ga_logs

    # ---------------- GA OPERATORS ----------------
    def tournament_select(self, population, k=4):
        candidates = random.sample(population, k)
        return max(candidates, key=lambda c: c.fitness)

    def crossover(self, g1, g2):
        point = random.randint(1, len(g1) - 2)
        return g1[:point] + g2[point:]

    def mutate(self, genes):
        for i in range(len(genes)):
            if random.random() < self.mutation_rate:
                low, high = DECISION_RANGES[i % len(DECISION_RANGES)]
                delta = random.uniform(-0.1 * (high - low), 0.1 * (high - low))
                genes[i] = max(low, min(high, genes[i] + delta))

    # ---------------- Visualization ----------------
    def visualize_evolution(self, history):
        print("\nEvolution Progress:")
        max_fit = max(history)
        for i, fit in enumerate(history, 1):
            bar = "█" * int(40 * fit / max_fit)
            print(f"Gen {i:3}: {bar} {fit:,.2f}")
