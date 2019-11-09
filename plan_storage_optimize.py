from itertools import combinations
from math import sqrt
import pandas as pd
from pycadical import Solver


class PlanStorage:
    def __init__(self, solver, items, max_storage):
        self.solver = solver
        self.items = items
        self.max_storage = max_storage

        self.item_count = len(self.items)
        self.day_count = self.items['end'].max() + 1

        self.var_count = 0
        self.clause_count = 0
        self.solution = None

        self.generate_constraints()

    def new_var(self):
        self.var_count += 1
        return self.var_count

    def add_clause(self, clause):
        self.clause_count += 1
        self.solver.add_clause(clause)

    def generate_constraints(self):
        self.place_each_item()
        self.limit_storage()
        self.no_overlap()

        for item_type in set(self.items['type']):
            self.separate_same_type(item_type)

    def place_each_item(self):
        self.placements = {}

        for item_id, item in self.items.iterrows():
            positions = self.max_storage - item.width + 1
            item_placements = [
                self.new_var() for position in range(0, positions)]

            self.exactly_one_of(item_placements)

            self.placements[item_id] = item_placements

    def limit_storage(self):
        self.limit_storage = [self.new_var() for i in range(self.max_storage)]

        for position, next in zip(self.limit_storage, self.limit_storage[1:]):
            self.add_clause([-position, next])

    def no_overlap(self):
        self.occupants = [
            [[limited] for limited in self.limit_storage]
            for day in range(self.day_count)]

        for item_id, item in self.items.iterrows():
            for day in range(item.begin, item.end + 1):
                for position, is_here in enumerate(self.placements[item_id]):
                    for i in range(item.width):
                        self.occupants[day][position + i].append(is_here)

        for days_occupants in self.occupants:
            for occupants in days_occupants:
                self.at_most_one_of(occupants)

    def separate_same_type(self, item_type):
        type_occupants = [
            [[] for i in range(self.max_storage + 1)]
            for day in range(self.day_count)]

        for item_id, item in self.items.iterrows():
            if item.type != item_type:
                continue

            for day in range(item.begin, item.end + 1):
                for position, is_here in enumerate(self.placements[item_id]):
                    for i in range(item.width + 1):
                        type_occupants[day][position + i].append(is_here)

        for days_occupants in type_occupants:
            for occupants in days_occupants:
                self.at_most_one_of(occupants)

    def exactly_one_of(self, literals):
        self.add_clause(literals)
        self.at_most_one_of(literals)

    def at_most_one_of(self, literals):
        if len(literals) < 16:
            for a, b in combinations(literals, 2):
                self.add_clause([-a, -b])
        else:
            rows = int(sqrt(len(literals)))
            columns = (len(literals) + rows - 1) // rows

            row_vars = [self.new_var() for i in range(rows)]
            column_vars = [self.new_var() for i in range(columns)]

            for i, row_var in enumerate(row_vars):
                for j, column_var in enumerate(column_vars):
                    k = i * columns + j
                    if k < len(literals):
                        input_var = literals[k]
                        self.add_clause([-input_var, row_var])
                        self.add_clause([-input_var, column_var])

            self.at_most_one_of(row_vars)
            self.at_most_one_of(column_vars)

    def solve(self):
        satisfiable = self.solver.solve()

        if satisfiable:
            self.store_solution()

        return satisfiable

    def store_solution(self):
        used_storage = self.max_storage - sum(
            self.solver.val(limited) for limited in self.limit_storage)

        placed_items = self.items.copy()

        placed_items['position'] = -1

        for item_id, item in placed_items.iterrows():
            for position, is_here in enumerate(self.placements[item_id]):
                if self.solver.val(is_here):
                    item.position = position
                    break

        self.solution = dict(
            used_storage=used_storage,
            placed_items=placed_items,
        )

    def improve_solution(self):
        used_storage = self.solution['used_storage']
        for i in range(used_storage - 1, self.max_storage):
            self.add_clause([self.limit_storage[i]])


if __name__ == '__main__':
    import argparse
    import time
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str)
    parser.add_argument('output', type=str)
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--max-storage', type=int, default=40)

    args = parser.parse_args()

    items = pd.read_csv(args.input, index_col='item_id')

    solver = Solver()
    if args.verbose:
        solver.set_option('report', 1)
    else:
        solver.set_option('quiet', 1)

    start = time.time()

    def print_ts(*args):
        print('%5.2f' % (time.time() - start), *args)

    plan_storage = PlanStorage(solver, items, args.max_storage)

    print_ts(
        plan_storage.var_count, 'variables,',
        plan_storage.clause_count, 'clauses',
    )

    print_ts('solving...')
    if plan_storage.solve():
        print_ts('solution found', plan_storage.solution['used_storage'])
    else:
        print_ts('no solution')
        sys.exit(1)

    try:
        plan_storage.improve_solution()
        while plan_storage.solve():
            print_ts(
                'solution improved', plan_storage.solution['used_storage'])
            plan_storage.improve_solution()
    except KeyboardInterrupt:
        print_ts('interrupted')
        pass
    else:
        print_ts('found optimum')

    plan_storage.solution['placed_items'].to_csv(args.output)
