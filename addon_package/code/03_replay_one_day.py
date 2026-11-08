"""Pure-Python, integer-micro-USDC replay of 2 June 2025 and its next 168 hours."""
import time
import pandas as pd
from common import OUT, read


def replay(fraction=25, order_name='large_first', record_trace=False):
    vaults = read('replay_example_vaults.csv').sort_values('vault')
    positions = read('replay_example_positions.csv')
    cash_table = read('replay_example_market_cash.csv')
    ledger = read('replay_example_ledger.csv').sort_values(['block', 'log_index'])
    assets = {r.vault: int(r.assets) for r in vaults.itertuples()}
    order = sorted(assets, key=lambda v: (-assets[v] if order_name=='large_first' else assets[v], v))
    cash = {r.market: int(r.cash) for r in cash_table.itertuples()}
    pos = {(r.vault, r.market): int(r.position) for r in positions.itertuples()}
    queues = {v: list(positions[positions.vault.eq(v)].sort_values('rank').market) for v in order}
    remaining = {v: assets[v]*fraction//100 for v in order}
    request = sum(remaining.values())
    initial_block, start = int(vaults.block.iloc[0]), int(vaults.timestamp.iloc[0])
    assert not ledger.duplicated(['block', 'log_index']).any()
    assert ledger.block.gt(initial_block).all() and ledger.block.le(initial_block+7*43200).all()
    assert ledger.timestamp.le(start+168*3600).all()
    assert ledger.sample_own_operation.eq(ledger.owner.isin(assets).astype(int)).all()
    payments, steps = [], []
    inflows = dict(Supply=0, Repay=0, Liquidation=0)
    clipped = 0

    def pay(block, log_index, timestamp):
        for vault in order:
            for market in queues[vault]:
                if remaining[vault] == 0:
                    break
                amount = min(remaining[vault], pos[(vault, market)], cash[market])
                if amount:
                    remaining[vault] -= amount
                    pos[(vault, market)] -= amount
                    cash[market] -= amount
                    if record_trace:
                        payments.append(dict(block=block, log_index=log_index, timestamp=timestamp,
                            vault=vault, market=market, paid_micro=amount,
                            vault_remaining_micro=remaining[vault], market_cash_after_micro=cash[market]))
        assert all(c>=0 for c in cash.values()) and all(p>=0 for p in pos.values())

    pay(initial_block, -1, start)
    initial_paid = request-sum(remaining.values())
    tau, censored = 0., False
    if sum(remaining.values()):
        tau, censored = 168., True
        for r in ledger.itertuples():
            if r.owner in assets:
                continue
            before = cash[r.market]
            amount = int(r.assets_micro)
            if r.kind in inflows:
                cash[r.market] += amount
                inflows[r.kind] += amount
                pay(int(r.block), int(r.log_index), int(r.timestamp))
                actual_delta = amount
            else:
                assert r.kind in ['Borrow', 'Withdraw']
                out = min(amount, cash[r.market])
                cash[r.market] -= out
                clipped += amount-out
                actual_delta = -out
            if record_trace:
                steps.append(dict(block=r.block, log_index=r.log_index, timestamp=r.timestamp, market=r.market,
                                  kind=r.kind, recorded_assets_micro=amount, applied_cash_delta_micro=actual_delta,
                                  market_cash_before_micro=before, market_cash_after_micro=cash[r.market],
                                  all_requests_remaining_micro=sum(remaining.values())))
            if not sum(remaining.values()):
                tau, censored = (int(r.timestamp)-start)/3600., False
                break
    paid = request-sum(remaining.values())
    if record_trace:
        OUT.mkdir(exist_ok=True)
        pd.DataFrame(payments).to_csv(OUT / 'replay_example_payments.csv', index=False)
        pd.DataFrame(steps).to_csv(OUT / 'replay_example_steps.csv', index=False)
    return dict(date=vaults.date.iloc[0], f=fraction, order=order_name, tau=tau, censored=censored,
                paid_fraction=paid/request, initial_paid_micro=initial_paid, request_micro=request,
                supply_inflow_micro=inflows['Supply'], repay_inflow_micro=inflows['Repay'],
                liquidation_inflow_micro=inflows['Liquidation'], clipped_outflow_micro=clipped)


def main():
    begin = time.perf_counter()
    rows = [replay(f, order, record_trace=(f==25 and order=='large_first'))
            for order in ['large_first', 'small_first'] for f in [10, 25]]
    OUT.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / 'replay_example_summary.csv', index=False)
    print(pd.DataFrame(rows)[['date', 'f', 'order', 'tau', 'censored', 'paid_fraction']].to_string(index=False))
    print(f'Single-day replay and integer payment trace finished in {time.perf_counter()-begin:.2f} seconds.')


if __name__ == '__main__':
    main()
