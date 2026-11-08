"""Extract the bounded CSV evidence package; never modifies research inputs."""
from pathlib import Path
import json, sqlite3, hashlib, gzip
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
O = ROOT / 'addon_stress_refill/out'
P = ROOT / 'addon_package'
SOURCE = Path('/Volumes/Extreme SSD/T9/JRF_Ryu_delivery/JRF_Manuscript_and_Replication 2/addon_stress_refill')
REPLICATION = SOURCE.parent / 'Replication_Package'
PROVENANCE = []


def save(df, name, source):
    path = P / 'data' / name
    df.to_csv(path, index=False, encoding='utf-8', float_format='%.17g')
    PROVENANCE.append(dict(file=name, source=source, rows=len(df), bytes=path.stat().st_size,
                           sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    print(name, len(df), path.stat().st_size, flush=True)


def windows(dates):
    t = pd.to_datetime(dates, utc=True)
    w1 = t.between('2025-10-09', '2025-10-17 23:59:59')
    w2 = t.between('2025-11-03', '2025-11-21 23:59:59')
    return dict(W1=w1, W2=w2,
                W1_control=t.between('2025-09-09', '2025-10-08 23:59:59'),
                W2_control=t.between('2025-10-04', '2025-11-02 23:59:59') & ~w1)


def run():
    for folder in ['data', 'code', 'output', 'check']:
        (P / folder).mkdir(parents=True, exist_ok=True)
    base = pd.read_csv(O / 'A1_daily_panel.csv')
    save(base, 'base_daily.csv', str(O / 'A1_daily_panel.csv'))
    hours = pd.concat([pd.read_csv(O / f'hourly_daily_{c}.csv') for c in [1, 42161, 8453]], ignore_index=True)
    save(hours, 'hourly_eth_arb_base.csv', str(O / 'hourly_daily_{1,42161,8453}.csv'))
    refill = pd.read_csv(O / 'B1_daily_replay.csv')
    save(refill[refill.order.eq('large_first') & refill.f.isin([10, 25])],
         'refill_daily.csv', str(O / 'B1_daily_replay.csv'))
    reference = pd.read_csv(O / 'joint_requests.csv')
    order = refill.merge(reference, on=['date', 'f'], validate='many_to_one')
    order['reference_zero'] = order.all_pass & ~order.excluded
    order['tau_zero'] = order.tau.eq(0)
    order['mismatch'] = order.reference_zero.ne(order.tau_zero)
    diag = pd.read_csv(O / 'B3_maxflow_diagnosis.csv')
    dc = ['date', 'f', 'max_flow_paid_micro', 'allocation_fully_feasible',
          'queue_order_feasible', 'feasible_queue_order', 'aggregate_bound_not_sufficient']
    order = order.merge(diag[dc], on=['date', 'f'], how='left', validate='many_to_one')
    save(order, 'refill_order_check.csv', str(O / 'B1_daily_replay.csv') + '; joint_requests.csv; B3_maxflow_diagnosis.csv')
    panel = pd.read_parquet(O / 'A3_hour_panel.parquet')
    panel = panel[panel.scope.eq('main')][['chain', 'utc', 'block', 'timestamp', 'vault', 'assets', 'capacity',
                                         'D', 'capacity_assets', 'Shared', 'W2', 'interaction']]
    save(panel, 'a4_unaffected_panel.csv', str(O / 'A3_hour_panel.parquet') + ' (main scope only; regression columns)')
    save(pd.read_csv(O / 'A3_related_markets.csv'), 'affected_collateral_list.csv', str(O / 'A3_related_markets.csv'))

    # Normalize saved, already screened and holder-vault-hour merged error events.
    base_e = pd.read_csv(O / 'A4_base_strict_events.csv')
    e = pd.DataFrame(dict(chain=8453, vault=base_e.vault, holder=base_e.owner,
                         request_micro=base_e.requested_assets_micro, block=base_e.block,
                         timestamp=base_e.timestamp, tx=base_e.tx, date=base_e.date,
                         resolved=~base_e.unresolved, wait_hours=base_e.wait_hours,
                         next_success_tx=base_e.next_success_tx))
    parts = [e]
    for c in [1, 42161]:
        z = pd.read_csv(O / f'A4_events_{c}.csv')
        z = z[z['filter'].eq('strict_claim')]
        parts.append(pd.DataFrame(dict(chain=c, vault=z.vault, holder=z.owner,
                         request_micro=z.request, block=z.block, timestamp=z.timestamp,
                         tx=z.tx, date=z.date, resolved=z.resolved, wait_hours=z.wait_hours,
                         next_success_tx=z.next_success_tx)))
    events = pd.concat(parts, ignore_index=True)
    masks = windows(events.date)
    for name, mask in masks.items():
        events[name] = mask.astype(int)
    events = events[events[list(masks)].any(axis=1)].copy()
    events['request_USDC'] = events.request_micro / 1e6
    success = {}
    for c in [1, 42161]:
        calls = pd.read_parquet(O / f'A4_calls_{c}.parquet')
        for r in calls[calls.committed.eq(True)].itertuples():
            success[(c, r.tx)] = int(r.block)
    db = REPLICATION / 'real_consequences/raw/events.sqlite'
    connection = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
    for tx in events.loc[events.chain.eq(8453), 'next_success_tx'].dropna().unique():
        row = connection.execute('select block from logs where tx=? limit 1', (tx,)).fetchone()
        if row is None:
            row = connection.execute('select block from calls where tx=? limit 1', (tx,)).fetchone()
        if row is not None:
            success[(8453, tx)] = row[0]
    connection.close()
    required = {(int(r.chain), r.next_success_tx) for r in events[events.resolved].itertuples()}
    missing = required - success.keys()
    # Follow-up log responses are the original evidence for events after W2 ends.
    inventory = pd.read_csv(O / 'rpc_response_inventory.csv')
    for path in inventory.loc[inventory.method.eq('eth_getLogs'), 'path']:
        if not missing:
            break
        z = json.loads(Path(path).read_text())
        chain = int(z['chain'])
        for log in z['response']['result']:
            key = (chain, log['transactionHash'])
            if key in missing:
                bn = log['blockNumber']
                success[key] = int(bn, 16) if isinstance(bn, str) else int(bn)
                missing.discard(key)
    for path in (SOURCE / 'out/portal_raw').glob('*.json.gz'):
        if not missing:
            break
        z = json.load(gzip.open(path, 'rt'))
        chain = int(z['chain'])
        if not any(c == chain for c, _ in missing):
            continue
        for packet in z['rows']:
            txs = {t['transactionIndex']: t['hash'] for t in packet.get('transactions', [])}
            for log in packet.get('logs', []):
                key = (chain, log.get('transactionHash') or txs[log['transactionIndex']])
                if key in missing:
                    success[key] = int(packet['header']['number'])
                    missing.discard(key)
    assert not missing, ('Missing successor block evidence', missing)
    events['next_success_block'] = pd.array([success.get((int(r.chain), r.next_success_tx))
                                             if r.resolved else None for r in events.itertuples()], dtype='Int64')
    events['next_success_timestamp'] = pd.array([round(r.timestamp + r.wait_hours * 3600)
                                                if r.resolved else None for r in events.itertuples()], dtype='Int64')
    save(events.sort_values(['chain', 'block', 'tx']), 'error_calls_windows.csv',
         str(O / 'A4_base_strict_events.csv') + '; A4_events_{1,42161}.csv; committed calls/logs for successor blocks')

    day = '2025-06-02'
    v = pd.read_parquet(O / 'vault_states.parquet')
    v = v[v.date.eq(day)].sort_values('vault')
    save(v[['date', 'block', 'timestamp', 'vault', 'assets']], 'replay_example_vaults.csv', str(O / 'vault_states.parquet') + f' ({day})')
    positions = pd.read_parquet(O / 'positions.parquet')
    save(positions[positions.date.eq(day)][['vault', 'market', 'rank', 'position']],
         'replay_example_positions.csv', str(O / 'positions.parquet') + f' ({day})')
    cash = pd.read_parquet(O / 'full_daily_market_cash.parquet')
    save(cash[cash.date.eq(day)][['market', 'cash']], 'replay_example_market_cash.csv', str(O / 'full_daily_market_cash.parquet') + f' ({day}, all 33 markets)')
    block = int(v.block.iloc[0])
    ledgerpath = REPLICATION / 'additional_evidence/panel_evidence/raw/market_operations.parquet'
    ledger = pd.read_parquet(ledgerpath, filters=[('block', '>', block), ('block', '<=', block + 7 * 43200)])
    ledger = ledger[['block', 'log_index', 'timestamp', 'tx', 'market', 'kind', 'owner', 'assets_micro']].sort_values(['block', 'log_index'])
    ledger['sample_own_operation'] = ledger.owner.isin(v.vault).astype(int)
    save(ledger, 'replay_example_ledger.csv', str(ledgerpath) + f' (blocks ({block},{block+7*43200}], one 168-hour example only)')
    pd.DataFrame(PROVENANCE).to_csv(P / 'check/source_manifest.csv', index=False)
    inputs = pd.read_csv(O / 'all_input_inventory.csv')
    raw = inputs[inputs.path.str.contains('/raw/') & ~inputs.path.str.endswith('.py')]
    (ROOT / 'addon_stress_refill/package_source_sizes.json').write_text(json.dumps(dict(
        raw_inputs_bytes=int(raw.bytes.sum()), full_operation_ledger_bytes=ledgerpath.stat().st_size,
        operation_ledger_rows=3949883, bounded_example_rows=len(ledger)), indent=2))


if __name__ == '__main__':
    run()
