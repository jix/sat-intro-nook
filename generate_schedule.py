import pandas as pd
import numpy as np
import random

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=100)
    parser.add_argument('--concurrent', type=int, default=20)
    parser.add_argument('--min-length', type=int, default=2)
    parser.add_argument('--max-length', type=int, default=20)
    parser.add_argument('--max-width', type=int, default=5)
    parser.add_argument('--prune', type=float, default=0.05)
    parser.add_argument('--types', type=int, default=4)
    parser.add_argument('output', type=str)

    args = parser.parse_args()

    tasks = []

    concurrent = np.zeros(args.days, dtype=int)

    candidates = list(range(args.days))
    random.shuffle(candidates)

    while candidates:
        if concurrent[candidates[-1]] >= args.concurrent:
            candidates.pop()
            continue

        selected = candidates[-1]

        low = high = selected

        limit_low = max(0, selected - args.max_length)
        while low > limit_low and concurrent[low - 1] < args.concurrent:
            low -= 1

        limit_high = min(args.days - 1, selected + args.max_length)
        while high < limit_high and concurrent[high + 1] < args.concurrent:
            high += 1

        if high - low + 1 < args.min_length:
            for day in range(low, high + 1):
                concurrent[day] = args.concurrent
            continue

        begin = random.randrange(low, high - args.min_length + 2)
        duration = random.randrange(
            args.min_length, min(high - begin + 2, args.max_length + 1))

        end = begin + duration - 1

        max_width = min(
            args.concurrent - concurrent[day]
            for day in range(begin, end + 1)
        )
        max_width = min(max_width, args.max_width)

        width = random.randrange(1, max_width + 1)

        for day in range(begin, end + 1):
            concurrent[day] += width

        type = random.randrange(args.types)

        tasks.append((begin, end, width, type))

    random.shuffle(tasks)

    tasks = tasks[round(len(tasks) * args.prune):]

    tasks = pd.DataFrame(
        sorted(tasks), columns=['begin', 'end', 'width', 'type'])
    tasks.index.name = 'item_id'
    tasks.to_csv(args.output)
