"""Same-transaction facility operations in completed institutional route censuses.

Deposits/withdrawals are operation labels, not tracing of fungible source units.
All matched arrival transactions, including those with no validated operation,
remain in the denominator. No estimates or sample dates are changed.
"""
from __future__ import annotations
import argparse
import gzip
import json

import pandas as pd

from revision6_collect_destinations import ROOT, OUT, sha
from revision4_collect_spark_cases import registry
from fetch_ethereum_full import TRANSFER_TOPIC, ZERO_TOPIC


def topic(address):
    return '0x' + address[2:].rjust(64, '0')


def signatures():
    old = json.loads((ROOT/'reports/revision4/spark_case_manifest.json').read_text())
    sig = {r['signature']: r['topic'] for r in old['items'] if 'signature' in r}
    for r in json.loads((ROOT/'data/raw/revision5/event_signatures.json').read_text()):
        assert sha(__import__('pathlib').Path(r['source'])) == r['sha256']
        sig[r['signature']] = r['topic']
    return sig


def analyze(domain):
    discovery = json.loads((OUT/f'domain_{domain}_discovery.json').read_text())
    manifest = json.loads((OUT/f'domain_{domain}_receipts.json').read_text())
    assert (discovery['complete_mint_discovery'] or discovery.get('complete_source_frame_search')) and manifest['complete_receipts']
    reg = registry()[domain]
    proxy, usdc, psm = reg['ALM_PROXY'], reg['USDC'], reg['PSM3']
    vault = reg.get('MORPHO_VAULT_SUSDC')
    sig = signatures()
    matches = pd.read_csv(OUT/f'domain_{domain}_matches.csv', dtype=str)
    assert len(matches) == discovery['source_events']
    matched = matches[matches.status.eq('exact_mint')]
    receipt_files = {x['tx_hash']: x for x in manifest['items']}
    rows, ops = [], []
    for tx, events in matched.groupby('destination_tx', sort=True):
        item = receipt_files[tx]; path = ROOT/item['file']
        assert sha(path) == item['sha256']
        receipt = json.load(gzip.open(path, 'rt'))['response']['result']
        assert receipt['transactionHash'] == tx and int(receipt['status'], 16) == 1
        logs = [{**x, 'index': int(x['logIndex'], 16)} for x in receipt['logs']]
        logs.sort(key=lambda x: x['index'])
        transfers = [x for x in logs if x['address'] == usdc and x['topics'][0] == TRANSFER_TOPIC]
        mint_indices = {int(x) for x in events.mint_log}
        assert len(mint_indices) == len(events)
        by_index = {x['index']: x for x in transfers}
        for r in events.itertuples():
            mint = by_index[int(r.mint_log)]
            assert mint['topics'] == [TRANSFER_TOPIC, ZERO_TOPIC, topic(proxy)]
            assert int(mint['data'], 16) == int(r.amount_micro_usdc)
        used_transfers = set(); tx_ops = []
        for log in logs:
            t = log['topics']; kind = None
            if not t:
                continue
            if log['address'] == psm and len(t) == 4:
                if t[0] == sig['Deposit(address,address,address,uint256,uint256)']:
                    kind = 'PSM deposit'
                elif t[0] == sig['Withdraw(address,address,address,uint256,uint256)']:
                    kind = 'PSM withdrawal'
                if kind and t[1:] != [topic(usdc), topic(proxy), topic(proxy)]:
                    kind = None
            elif vault and log['address'] == vault:
                if t[0] == sig['Deposit(address,address,uint256,uint256)'] and t[1:] == [topic(proxy), topic(proxy)]:
                    kind = 'Vault deposit'
                elif t[0] == sig['Withdraw(address,address,address,uint256,uint256)'] and t[2:] == [topic(proxy), topic(proxy)]:
                    kind = 'Vault withdrawal'
            if kind is None:
                continue
            raw = bytes.fromhex(log['data'][2:]); assert len(raw) == 64
            amount, shares = int.from_bytes(raw[:32]), int.from_bytes(raw[32:])
            assert amount > 0 and shares > 0
            deposit = kind.endswith('deposit')
            sender, receiver = (proxy, log['address']) if deposit else (log['address'], proxy)
            token_links = [x for x in transfers if x['topics'][1:] == [topic(sender), topic(receiver)]
                           and int(x['data'], 16) == amount and x['index'] < log['index']
                           and x['index'] not in used_transfers]
            chosen = max(token_links, key=lambda x: x['index']) if token_links else None
            if chosen:
                used_transfers.add(chosen['index'])
            op = {'domain': domain, 'destination_tx': tx, 'operation': kind,
                  'facility': log['address'], 'operation_log': log['index'],
                  'amount_micro_usdc': str(amount), 'share_base_units': str(shares),
                  'native_transfer_log': None if chosen is None else chosen['index'],
                  'validated_native_transfer': chosen is not None,
                  'after_first_frame_mint': bool(chosen and chosen['index'] > min(mint_indices)),
                  'after_all_frame_mints': bool(chosen and chosen['index'] > max(mint_indices)),
                  'scope': 'Co-occurring operation; no attribution of fungible minted units'}
            ops.append(op); tx_ops.append(op)
        valid = [x for x in tx_ops if x['validated_native_transfer']]
        mint_logs = [x for x in transfers if x['topics'][1:] == [ZERO_TOPIC, topic(proxy)]]
        inflow = sum(int(x['data'], 16) for x in transfers if x['topics'][2] == topic(proxy) and x['topics'][1] != topic(proxy))
        outflow = sum(int(x['data'], 16) for x in transfers if x['topics'][1] == topic(proxy) and x['topics'][2] != topic(proxy))
        rows.append({'domain': domain, 'destination_tx': tx,
                     'source_burns': len(events), 'source_micro_usdc': str(sum(int(x) for x in events.amount_micro_usdc)),
                     'mint_events_to_proxy': len(mint_logs),
                     'mint_micro_usdc_to_proxy': str(sum(int(x['data'], 16) for x in mint_logs)),
                     'validated_deposits': sum(x['operation'].endswith('deposit') for x in valid),
                     'validated_withdrawals': sum(x['operation'].endswith('withdrawal') for x in valid),
                     'operations_without_native_link': len(tx_ops)-len(valid),
                     'proxy_in_micro': str(inflow), 'proxy_out_micro': str(outflow),
                     'proxy_change_micro': str(inflow-outflow)})
    frame_micro = sum(int(x) for x in matches.amount_micro_usdc)
    delay = matched.destination_timestamp.astype(int) - matched.source_timestamp.astype(int)
    summary = {'domain': domain, 'complete_route_discovery': True,
               'source_burns': len(matches), 'source_micro_usdc': str(frame_micro),
               'matched_burns': len(matched),
               'matched_micro_usdc': str(sum(int(x) for x in matched.amount_micro_usdc)),
               'unmatched_by_cutoff': int(matches.status.ne('exact_mint').sum()),
               'destination_transactions': len(rows),
               'transactions_with_validated_deposit': sum(x['validated_deposits'] > 0 for x in rows),
               'transactions_with_validated_withdrawal': sum(x['validated_withdrawals'] > 0 for x in rows),
               'transactions_without_validated_operation': sum(x['validated_deposits'] + x['validated_withdrawals'] == 0 for x in rows),
               'unlinked_operations': sum(not x['validated_native_transfer'] for x in ops),
               'delay_seconds': {'median': float(delay.median()), 'max': int(delay.max())},
               'operations': {},
               'scope': 'Selected institution and route; same-transaction co-occurrence, not ultimate use or funding provenance'}
    for name in ['PSM deposit', 'PSM withdrawal', 'Vault deposit', 'Vault withdrawal']:
        selected = [x for x in ops if x['operation'] == name and x['validated_native_transfer']]
        summary['operations'][name] = {'events': len(selected),
            'amount_micro_usdc': str(sum(int(x['amount_micro_usdc']) for x in selected)),
            'after_all_frame_mints': sum(x['after_all_frame_mints'] for x in selected)}
    pd.DataFrame(rows).to_csv(OUT/f'domain_{domain}_operations_transactions.csv', index=False)
    operations_frame=pd.DataFrame(ops)
    if len(operations_frame):
        operations_frame['native_transfer_log']=pd.array(
            [r['native_transfer_log'] for r in ops],dtype='Int64')
    operations_frame.to_csv(OUT/f'domain_{domain}_operations.csv', index=False)
    (OUT/f'domain_{domain}_operations_summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))
    if domain == 6:
        from revision6_market_links import analyze as market_links
        market_links()


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--domains', nargs='+', type=int, required=True)
    for d in p.parse_args().domains:
        analyze(d)
