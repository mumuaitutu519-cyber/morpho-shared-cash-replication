"""Exhaustive artificial integer fixtures, never empirical observations.

An independent dynamic program enumerates every feasible focal-unit allocation.
It neither calls the reported-bound algorithm nor solves its linear program.
The output records software-test coverage only; no simulated research data,
coefficients or p-values are produced.
"""
from collections import Counter
import json

from revision6_first_disposition import extrema
from revision6_collect_destinations import OUT


def enumerate_allocations(initial, events):
    # State: remaining focal units, cumulative focal units at target departures.
    states = {(0, 0)}
    cash = initial
    for event in events:
        amount = event['amount']
        if event['kind'] == 'focal_in':
            cash += amount
            states = {(focal + amount, target) for focal, target in states}
        elif event['kind'] == 'other_in':
            cash += amount
        else:
            next_states = set()
            for focal, target in states:
                alternative = cash - focal
                for take in range(max(0, amount - alternative), min(focal, amount) + 1):
                    next_states.add((focal - take, target + take * event['target']))
            cash -= amount
            states = next_states
        assert cash >= 0 and states
        assert all(0 <= focal <= cash for focal, _ in states)
    return min(x[1] for x in states), max(x[1] for x in states)


def main():
    counts = Counter()

    def visit(initial, events, cash, depth):
        expected = enumerate_allocations(initial, events)
        actual = tuple(extrema(initial, events, maximize)[0] for maximize in [False, True])
        assert actual == expected, (initial, events, expected, actual)
        counts[len(events)] += 1
        if depth == 0:
            return
        for amount in [1, 2]:
            for kind in ['focal_in', 'other_in']:
                visit(initial, events + [{'kind': kind, 'amount': amount}], cash + amount, depth - 1)
            if amount <= cash:
                for target in [False, True]:
                    visit(initial, events + [{'kind': 'out', 'amount': amount, 'target': target}],
                          cash - amount, depth - 1)

    for initial in [0, 1, 2]:
        visit(initial, [], initial, 6)
    result = {'status': 'PASS', 'fixture_type': 'ARTIFICIAL SOFTWARE TESTS ONLY',
              'comparison': 'Reported greedy bounds versus exhaustive feasible integer allocations',
              'initial_balances': [0, 1, 2], 'positive_event_amounts': [1, 2],
              'max_events': 6, 'fixtures_by_length': dict(sorted(counts.items())),
              'fixtures_checked': sum(counts.values()),
              'scope': 'Finite test coverage, not a proof for arbitrary inputs or empirical evidence'}
    (OUT / 'funding_bounds_software_tests.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
