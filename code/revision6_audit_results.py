"""Offline revision-6 evidence audit; no API requests or fitted specifications."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/revision6'


def checked(item):
    path = ROOT / item['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], path
    return json.load(gzip.open(path, 'rt')) if path.suffix == '.gz' else json.loads(path.read_text())


def uint(raw, offset):
    assert offset >= 0 and offset + 32 <= len(raw)
    return int.from_bytes(raw[offset:offset + 32])


def capacity():
    manifest = json.loads((OUT/'withdrawal_capacity_manifest.json').read_text())
    assert manifest['complete_fixed_window'] and manifest['days'] == 320
    rows = manifest['items']
    assert [r['date'] for r in rows] == list(pd.date_range('2025-01-15', '2025-11-30').strftime('%Y-%m-%d'))
    csv = pd.read_csv(OUT/'withdrawal_capacity.csv', dtype=str)
    api = pd.read_csv(ROOT/'reports/revision5/vault_ownership_validation.csv', dtype=str)
    api = {int(r.timestamp): r for r in api.itertuples()}
    share_gaps, total_gaps, claim_gaps = [], [], []
    count = 0
    for r, tab in zip(rows, csv.to_dict('records'), strict=True):
        for key in ['date', 'block', 'block_hash', 'treasury_shares', 'total_shares',
                    'claim_micro', 'max_withdraw_micro', 'shortfall_micro']:
            assert str(r[key]) == tab[key]
        responses = []
        for item in r['files']:
            obj = checked(item); count += 1
            requests = obj['request']['payload']
            assert isinstance(requests, list)
            by_id = {x['id']: x for x in obj['response']}
            for req in requests:
                assert req['method'] in {'eth_getBlockByNumber', 'eth_getCode', 'eth_call'}
                ans = by_id[req['id']]
                assert 'error' not in ans and ans.get('result') is not None
                responses.append((req, ans['result']))
        headers = {int(a['number'], 16): a for q, a in responses if q['method'] == 'eth_getBlockByNumber'}
        b = int(r['block']); before, after = headers[b], headers[b+1]
        assert before['hash'] == r['block_hash'] == after['parentHash']
        assert int(before['timestamp'], 16) == r['block_timestamp']
        assert int(after['timestamp'], 16) == r['next_block_timestamp']
        assert r['block_timestamp'] < r['boundary_timestamp'] <= r['next_block_timestamp']
        codes = [a for q, a in responses if q['method'] == 'eth_getCode']
        assert len(codes) == 1 and len(codes[0]) > 2
        assert hashlib.sha256(bytes.fromhex(codes[0][2:])).hexdigest() == r['runtime_code_sha256']
        calls = [(q, a) for q, a in responses if q['method'] == 'eth_call']
        multicall = [(q, a) for q, a in calls if q['params'][0]['data'].startswith('0xac9650d8')]
        assert len(multicall) == 1
        q, result = multicall[0]
        assert int(q['params'][1], 16) == b
        raw = bytes.fromhex(result[2:]); start = uint(raw, 0)
        assert uint(raw, start) == 6
        decoded = []
        for j in range(6):
            pos = start + 32 + uint(raw, start + 32 + j*32)
            assert uint(raw, pos) == 32
            decoded.append(uint(raw, pos+32))
        for value, field in zip(decoded[:4], ['treasury_shares', 'total_shares', 'total_assets_micro', 'max_withdraw_micro']):
            assert value == int(r[field])
        assert f'0x{decoded[4]:040x}' == r['fee_recipient']
        # The API argument and independently returned on-chain ownership agree
        # on every date in these archived data, so the conversion is direct.
        a = api[r['boundary_timestamp']]
        share_gaps.append(int(r['treasury_shares'])-int(a.api_treasury_shares))
        assert share_gaps[-1] == 0 and decoded[5] == int(r['claim_micro'])
        total_gaps.append(int(r['total_shares'])-int(a.api_total_shares))
        # A diagnostic, not a replacement for the block-specific contract view.
        claim_gaps.append(int(r['treasury_shares'])*(int(r['total_assets_micro'])+1)
                          //(int(a.api_total_shares)+10**12)-int(r['claim_micro']))
        c, w = int(r['claim_micro']), int(r['max_withdraw_micro'])
        assert 0 <= w <= c and c-w == int(r['shortfall_micro'])
        assert abs(w/c-r['withdrawable_fraction']) < 1e-15
    sample = rows[1:]
    fraction = pd.Series([int(r['max_withdraw_micro'])/int(r['claim_micro']) for r in sample])
    summary = json.loads((OUT/'withdrawal_capacity_summary.json').read_text())
    assert summary['days'] == len(sample) == 319
    assert summary['capacity_below_claim_days'] == sum(int(r['shortfall_micro']) > 0 for r in sample)
    for key, number in [('min', fraction.min()), ('median', fraction.median()), ('max', fraction.max()), ('end', fraction.iloc[-1])]:
        assert abs(summary['fraction'][key]-number) < 1e-15
    return {'status': 'PASS', 'dates': 320, 'primary_days': 319, 'raw_files_checked': count,
            'minimum_positive_shortfall_micro':str(min(int(r['shortfall_micro']) for r in sample if int(r['shortfall_micro'])>0)),
            'all_treasury_shares_equal_api': all(x == 0 for x in share_gaps),
            'total_share_gap_days': sum(x != 0 for x in total_gaps),
            'max_relative_total_share_gap': max(abs(g)/(int(r['total_shares'])-g) for g,r in zip(total_gaps,rows)),
            'api_total_reconstruction_claim_gap_micro_min': min(claim_gaps),
            'api_total_reconstruction_claim_gap_micro_max': max(claim_gaps),
            'provider_difference_status': 'Retained, not attributed conclusively to accrual or timing',
            'withdrawal_capacity': summary}


def first_disposition(domain):
    from revision4_collect_spark_cases import registry
    from fetch_ethereum_full import TRANSFER_TOPIC
    from scipy.optimize import linprog
    import numpy as np

    obj = json.loads((OUT/f'domain_{domain}_first_disposition_manifest.json').read_text())
    rows, summary = obj['items'], obj['summary']
    frame = pd.read_csv(OUT/f'domain_{domain}_matches.csv', dtype=str)
    assert frame.status.eq('exact_mint').all()
    assert len(rows) == frame.destination_tx.nunique() == summary['transactions']
    assert {r['destination_tx'] for r in rows} == set(frame.destination_tx)
    reg = registry()[domain]
    proxy, usdc = reg['ALM_PROXY'], reg['USDC']
    padded = lambda address: '0x' + address[2:].rjust(64, '0')
    receipt_manifest = json.loads((OUT/f'domain_{domain}_receipts.json').read_text())
    receipt_files = {item['tx_hash']: item for item in receipt_manifest['items']}
    operations = pd.read_csv(OUT/f'domain_{domain}_operations.csv', dtype=str)
    market_links = pd.read_csv(OUT/'domain_6_market_links.csv', dtype=str) if domain == 6 else None
    max_replay_error = 0.0

    def linear_state_bounds(initial, events):
        # Independent formulation: explicit retained-cohort states and departure
        # variables, with equality constraints for every outflow transition.
        cash, pending_focal, outs = initial, 0, []
        for event in events:
            if event['kind'] != 'out':
                cash += event['amount']
                pending_focal += event['amount'] * (event['kind'] == 'focal_in')
            else:
                cash -= event['amount']
                outs.append((pending_focal, cash, event['amount'], event['target']))
                pending_focal = 0
        n = len(outs)
        if n == 0:
            return (0.0, 0.0)
        matrix = np.zeros((n, 2*n))
        for j in range(n):
            matrix[j, j] = matrix[j, n+j] = 1.0
            if j:
                matrix[j, j-1] = -1.0
        rhs = np.array([x[0]/1e6 for x in outs])
        limits = [(0, x[1]/1e6) for x in outs] + [(0, x[2]/1e6) for x in outs]
        objective = np.array([0.0]*n + [float(x[3]) for x in outs])
        values = []
        for sign in [1, -1]:
            fit = linprog(sign*objective, A_eq=matrix, b_eq=rhs, bounds=limits,
                          method='highs', options={'primal_feasibility_tolerance': 1e-8,
                                                  'dual_feasibility_tolerance': 1e-8})
            assert fit.success, fit.message
            values.append(sign*fit.fun)
        return tuple(values)

    for r in rows:
        tx, block = r['destination_tx'], int(r['block'])
        receipt = checked(receipt_files[tx])['response']['result']
        assert receipt['transactionHash'] == tx and int(receipt['status'], 16) == 1
        assert receipt['blockHash'] == r['block_hash'] and int(receipt['blockNumber'], 16) == block
        balances, block_logs = {}, None
        for item in r['files']:
            raw = checked(item)
            request, response = raw['request']['payload'], raw['response']
            assert 'error' not in response and response.get('result') is not None
            if request['method'] == 'eth_call':
                call, at = request['params']
                assert call == {'to': usdc, 'data': '0x70a08231' + proxy[2:].rjust(64, '0')}
                at = int(at, 16)
                assert at not in balances and at in {block-1, block}
                assert len(response['result']) == 66
                balances[at] = int(response['result'], 16)
            else:
                assert request['method'] == 'eth_getLogs' and block_logs is None
                query = request['params'][0]
                assert query == {'fromBlock': hex(block), 'toBlock': hex(block),
                                 'address': usdc, 'topics': [TRANSFER_TOPIC]}
                block_logs = response['result']
        assert set(balances) == {block-1, block} and block_logs is not None
        log_keys = []
        for log in block_logs:
            assert log['address'] == usdc and log['topics'][0] == TRANSFER_TOPIC
            assert len(log['topics']) == 3 and len(log['data']) == 66
            assert int(log['blockNumber'], 16) == block and log['blockHash'] == r['block_hash']
            assert not log.get('removed', False)
            log_keys.append(int(log['logIndex'], 16))
        assert len(log_keys) == len(set(log_keys))
        block_logs.sort(key=lambda log: int(log['logIndex'], 16))
        delta = lambda log: int(log['data'], 16) * (
            int(log['topics'][2] == padded(proxy)) - int(log['topics'][1] == padded(proxy)))
        assert balances[block] - balances[block-1] == sum(delta(log) for log in block_logs)
        first_log = min(int(log['logIndex'], 16) for log in receipt['logs'])
        opening = balances[block-1] + sum(delta(log) for log in block_logs
                                         if int(log['logIndex'], 16) < first_log)
        assert opening == int(r['opening_balance_micro'])
        selected = [log for log in block_logs if log['transactionHash'] == tx]
        key = lambda log: (int(log['logIndex'], 16), tuple(log['topics']), log['data'])
        assert sorted(map(key, selected)) == sorted(key(log) for log in receipt['logs']
                                                    if log['address'] == usdc and log['topics'][0] == TRANSFER_TOPIC)
        cohort = frame[frame.destination_tx.eq(tx)]
        focal_logs = {int(row.mint_log): int(row.amount_micro_usdc) for row in cohort.itertuples()}
        valid_ops = operations[operations.destination_tx.eq(tx) & operations.validated_native_transfer.eq('True')]
        target_sets = {label: set(valid_ops.loc[valid_ops.operation.eq(name), 'native_transfer_log'].astype(int))
                       for label, name in [('psm', 'PSM deposit'), ('vault', 'Vault deposit')]}
        targets = target_sets['psm'] | target_sets['vault']
        assert not target_sets['psm'] & target_sets['vault']
        events = []
        for log in selected:
            index, change = int(log['logIndex'], 16), delta(log)
            if index in focal_logs:
                assert change == focal_logs[index]
                events.append({'kind': 'focal_in', 'amount': change, 'log_index': index})
            elif change > 0:
                events.append({'kind': 'other_in', 'amount': change, 'log_index': index})
            elif change < 0:
                events.append({'kind': 'out', 'amount': -change, 'target': index in targets, 'log_index': index})
        assert events == r['events']
        assert targets <= {e['log_index'] for e in events if e['kind'] == 'out'}
        checks = {'combined': (events, r)}
        if domain == 6:
            linked = market_links[market_links.destination_tx.eq(tx) & market_links.linked_market_supply.eq('True')]
            target_sets['credit_linked'] = set(linked.deposit_native_transfer_log.astype(int))
            assert target_sets['credit_linked'] <= target_sets['vault']
            assert set(r['operation_bounds']) == set(target_sets)
            for label, target_indices in target_sets.items():
                selected_events = [{**e, 'target': e['log_index'] in target_indices} if e['kind'] == 'out' else e
                                   for e in events]
                checks[label] = selected_events, r['operation_bounds'][label]
        for selected_events, bounds in checks.values():
            lo, hi = linear_state_bounds(opening, selected_events)
            error = max(abs(lo - int(bounds['lower_micro'])/1e6), abs(hi - int(bounds['upper_micro'])/1e6))
            tolerance = 1e-5 + 1e-12 * max(opening, sum(e['amount'] for e in events))/1e6
            assert error <= tolerance, (tx, error, tolerance)
            max_replay_error = max(max_replay_error, error)
        if domain == 6:
            bounds = r['operation_bounds']
            for edge in ['lower_micro', 'upper_micro']:
                assert int(bounds['credit_linked'][edge]) <= int(bounds['vault'][edge]) <= int(r[edge])
                assert int(bounds['psm'][edge]) <= int(r[edge])
            assert sum(int(bounds[k]['lower_micro']) for k in ['psm', 'vault']) <= int(r['lower_micro'])
            assert int(r['upper_micro']) <= sum(int(bounds[k]['upper_micro']) for k in ['psm', 'vault'])
        cash = int(r['opening_balance_micro']); focal = deposits = 0
        indices = []
        for e in r['events']:
            indices.append(e['log_index']); amount = e['amount']
            assert isinstance(amount, int) and amount > 0
            if e['kind'] == 'out':
                cash -= amount; deposits += amount*e['target']
            else:
                cash += amount; focal += amount*(e['kind'] == 'focal_in')
            assert cash >= 0
        assert indices == sorted(set(indices))
        assert focal == int(r['frame_micro']) and deposits == int(r['validated_deposit_micro'])
        assert 0 <= int(r['lower_micro']) <= int(r['upper_micro']) <= min(focal, deposits)
        assert r['lp_validation']['max_error_usdc'] <= r['lp_validation']['tolerance_usdc']
        if r['opening_balance_micro'] == '0' and all(e['kind'] != 'other_in' for e in r['events']):
            assert int(r['lower_micro']) == int(r['upper_micro']) == deposits
    for field in ['frame_micro', 'validated_deposit_micro', 'lower_micro', 'upper_micro']:
        assert sum(int(r[field]) for r in rows) == int(summary[field])
    assert sum(r['frame_mints'] for r in rows) == len(frame) == summary['frame_burns']
    if domain == 6:
        for label in ['psm', 'vault', 'credit_linked']:
            for edge in ['lower_micro', 'upper_micro']:
                assert sum(int(r['operation_bounds'][label][edge]) for r in rows) == int(summary['operation_bounds'][label][edge])
    return {'status': 'PASS', **summary,
            'raw_balance_and_transfer_replay': 'PASS',
            'independent_state_equality_lp_max_error_usdc': max_replay_error,
            'lower_share_of_arrivals': int(summary['lower_micro'])/int(summary['frame_micro']),
            'upper_share_of_arrivals': int(summary['upper_micro'])/int(summary['frame_micro']),
            'lower_share_of_deposits': (int(summary['lower_micro'])/int(summary['validated_deposit_micro'])
                                        if int(summary['validated_deposit_micro']) else None),
            'upper_share_of_deposits': (int(summary['upper_micro'])/int(summary['validated_deposit_micro'])
                                        if int(summary['validated_deposit_micro']) else None)}


def market_supply_links():
    """Replay all reported Base vault-deposit links, retaining unlinked rows."""
    path = OUT/'domain_6_market_links.csv'
    if not path.exists():
        return {'status': 'INCOMPLETE_COLLECTION'}
    from revision4_collect_spark_cases import registry
    from revision6_destination_operations import signatures
    from revision5_collect_liquidity import MARKET
    from fetch_ethereum_full import TRANSFER_TOPIC

    reg, sig = registry()[6], signatures()
    proxy, vault, morpho, usdc = (reg[k] for k in ['ALM_PROXY', 'MORPHO_VAULT_SUSDC', 'MORPHO', 'USDC'])
    topic = lambda address: '0x' + address[2:].rjust(64, '0')
    links = pd.read_csv(path, dtype=str)
    operations = pd.read_csv(OUT/'domain_6_operations.csv', dtype=str)
    deposits = operations[operations.operation.eq('Vault deposit') & operations.validated_native_transfer.eq('True')]
    expected = {(row.destination_tx, int(row.operation_log)): row for row in deposits.itertuples()}
    actual = [(row.destination_tx, int(row.deposit_log)) for row in links.itertuples()]
    assert len(expected) == len(deposits) == len(actual) == len(set(actual)) and set(actual) == set(expected)
    manifest = json.loads((OUT/'domain_6_receipts.json').read_text())
    records = {row['tx_hash']: row for row in manifest['items']}
    receipts = {tx: checked(records[tx])['response']['result'] for tx in set(links.destination_tx)}
    seen_supply, seen_transfer = set(), set()
    linked_micro = 0
    for row in sorted(links.itertuples(), key=lambda value: (value.destination_tx, int(value.deposit_log))):
        deposit = expected[row.destination_tx, int(row.deposit_log)]
        assert row.market_id == MARKET and row.linked_market_supply in {'True', 'False'}
        assert row.amount_micro == deposit.amount_micro_usdc
        assert int(row.deposit_native_transfer_log) == int(deposit.native_transfer_log)
        logs = {int(log['logIndex'], 16): log for log in receipts[row.destination_tx]['logs']}
        event, payment = logs[int(row.deposit_log)], logs[int(row.deposit_native_transfer_log)]
        assert event['address'] == vault and event['topics'] == [sig['Deposit(address,address,uint256,uint256)'], topic(proxy), topic(proxy)]
        body = bytes.fromhex(event['data'][2:])
        assert len(body) == 64 and uint(body, 0) == int(row.amount_micro) and uint(body, 32) > 0
        assert payment['address'] == usdc and payment['topics'] == [TRANSFER_TOPIC, topic(proxy), topic(vault)]
        assert int(payment['data'], 16) == int(row.amount_micro)
        assert int(row.deposit_native_transfer_log) < int(row.deposit_log)
        later_ops = [index for index, log in logs.items() if index > int(row.deposit_log)
                     and log['address'] == vault and log['topics'] and log['topics'][0] in {
                         sig['Deposit(address,address,uint256,uint256)'],
                         sig['Withdraw(address,address,address,uint256,uint256)']}]
        stop = min(later_ops) if later_ops else float('inf')
        feasible = []
        for index, candidate in logs.items():
            if not int(row.deposit_log) < index < stop or (row.destination_tx, index) in seen_supply:
                continue
            if candidate['address'] != morpho or candidate['topics'] != [
                    sig['Supply(bytes32,address,address,uint256,uint256)'], MARKET, topic(vault), topic(vault)]:
                continue
            body = bytes.fromhex(candidate['data'][2:])
            assert len(body) == 64
            if uint(body, 0) != int(row.amount_micro) or uint(body, 32) <= 0:
                continue
            for payment_index, candidate_payment in logs.items():
                if not index < payment_index < stop or (row.destination_tx, payment_index) in seen_transfer:
                    continue
                if candidate_payment['address'] == usdc and candidate_payment['topics'] == [
                        TRANSFER_TOPIC, topic(vault), topic(morpho)] and int(candidate_payment['data'], 16) == int(row.amount_micro):
                    feasible.append((index, payment_index))
        if row.linked_market_supply == 'False':
            assert pd.isna(row.supply_log) and pd.isna(row.supply_native_transfer_log)
            assert not feasible, 'A qualifying market supply was labeled unlinked'
            continue
        supply_index, transfer_index = int(row.supply_log), int(row.supply_native_transfer_log)
        assert feasible and (supply_index, transfer_index) == min(feasible)
        supply, transfer = logs[supply_index], logs[transfer_index]
        assert supply['address'] == morpho
        assert supply['topics'] == [sig['Supply(bytes32,address,address,uint256,uint256)'], MARKET, topic(vault), topic(vault)]
        body = bytes.fromhex(supply['data'][2:])
        assert len(body) == 64 and uint(body, 0) == int(row.amount_micro) and uint(body, 32) > 0
        assert transfer['address'] == usdc and transfer['topics'] == [TRANSFER_TOPIC, topic(vault), topic(morpho)]
        assert int(transfer['data'], 16) == int(row.amount_micro)
        assert int(row.deposit_log) < supply_index < transfer_index
        assert not later_ops or transfer_index < min(later_ops)
        for seen, index in [(seen_supply, supply_index), (seen_transfer, transfer_index)]:
            key = row.destination_tx, index
            assert key not in seen
            seen.add(key)
        linked_micro += int(row.amount_micro)
    summary = json.loads((OUT/'domain_6_market_links_summary.json').read_text())
    assert summary['vault_deposits'] == len(links)
    assert summary['linked_deposits'] == len(seen_supply)
    assert int(summary['all_deposit_micro']) == sum(int(x) for x in links.amount_micro)
    assert int(summary['linked_deposit_micro']) == linked_micro
    return {'status': 'PASS', **summary, 'unlinked_rows_retained': len(links)-len(seen_supply),
            'positive_and_negative_link_replay': 'PASS'}


def completed_routes():
    from revision4_collect_spark_cases import registry, REG
    from fetch_ethereum_full import TRANSFER_TOPIC, ZERO_TOPIC
    contract_registry=registry()
    frame = pd.read_parquet(ROOT/'reports/revision4/spark_source_burns.parquet')
    assert len(frame) == 4369
    source = {(r.transaction_hash, int(r.log_index)): r for r in frame.itertuples()}
    assert len(source) == len(frame)
    received = '0x58200b4c34ae05ee816d710053fff3fb75af4395915d3d2a771b24aa10e3cc5d'
    sender = bytes.fromhex('bd3fa81b58ba92a82136038b25adec7066af3155'.rjust(64,'0'))
    result = {}
    for domain in [2,3,6,10]:
        filename = OUT/f'domain_{domain}_matches.csv'
        if not filename.exists():
            result[str(domain)] = {'status':'INCOMPLETE_COLLECTION', 'source_burns':int(frame.destination_domain.eq(domain).sum())}
            continue
        rows = pd.read_csv(filename,dtype=str)
        assert rows.status.eq('exact_mint').all()
        manifest = json.loads((OUT/f'domain_{domain}_receipts.json').read_text())
        lookup = {r['tx_hash']:r for r in manifest['items']}
        extra_headers = {}
        extra_path = OUT/f'domain_{domain}_header_validation.json'
        if extra_path.exists():
            extra = json.loads(extra_path.read_text()); assert extra['complete'] and extra['status']=='PASS'
            extra_headers = {r['tx_hash']:r for r in extra['items']}
        receipts, headers = {}, {}
        for tx in set(rows.destination_tx):
            item = lookup[tx]
            receipts[tx] = checked(item)['response']['result']
            hitem = ({'file':item['header_file'],'sha256':item['header_sha256']}
                     if 'header_file' in item else extra_headers[tx])
            headers[tx] = checked(hitem)['response']['result']
        keys = []; mint_keys = []; values = 0
        for row in rows.itertuples():
            key = row.source_tx, int(row.source_log); keys.append(key); original = source[key]
            assert int(original.destination_domain) == domain and int(original.version) == 1
            assert int(original.amount_micro_usdc) == int(row.amount_micro_usdc)
            assert int(original.nonce_hex,16) == int(row.nonce)
            receipt, header = receipts[row.destination_tx], headers[row.destination_tx]
            assert receipt['transactionHash'] == row.destination_tx and int(receipt['status'],16) == 1
            assert receipt['blockHash'] == header['hash'] and int(header['number'],16) == int(row.destination_block)
            assert int(original.timestamp) == int(row.source_timestamp) <= int(header['timestamp'],16) < 1764547200
            assert int(header['timestamp'],16) == int(row.destination_timestamp)
            logs = {int(x['logIndex'],16):x for x in receipt['logs']}
            assert len(logs) == len(receipt['logs'])
            protocol, mint = logs[int(row.receipt_log)], logs[int(row.mint_log)]
            assert protocol['address'] == REG[str(domain)]['transmitter'] and protocol['topics'][0] == received
            assert int(protocol['topics'][2],16) == int(row.nonce)
            raw = bytes.fromhex(protocol['data'][2:]); offset = uint(raw,64); size = uint(raw,offset)
            assert uint(raw,0) == 0 and raw[32:64] == sender
            assert '0x'+raw[offset+32:offset+32+size].hex() == original.body_hex
            assert mint['address'] == contract_registry[domain]['USDC']
            assert mint['topics'] == [TRANSFER_TOPIC,ZERO_TOPIC,original.mint_recipient]
            assert int(mint['data'],16) == int(original.amount_micro_usdc)
            assert int(row.mint_log) < int(row.receipt_log)
            mint_keys.append((row.destination_tx,int(row.mint_log))); values += int(row.amount_micro_usdc)
        expected = {key for key,r in source.items() if int(r.destination_domain) == domain}
        assert len(keys) == len(set(keys)) and set(keys) == expected
        assert len(mint_keys) == len(set(mint_keys))
        result[str(domain)] = {'status':'PASS','source_burns':len(rows),
                               'destination_transactions':len(receipts),'amount_micro':str(values)}
    return result


if __name__ == '__main__':
    from revision6_audit_operations import audit as audit_operations
    result = {'capacity': capacity(), 'routes': {}, 'completion':completed_routes(),
              'base_market_supply_links': market_supply_links(),
              'facility_operations': {str(domain): audit_operations(domain) for domain in [2, 3, 6, 10]}}
    for domain in [2, 3, 6, 10]:
        if (OUT/f'domain_{domain}_first_disposition_manifest.json').exists():
            result['routes'][str(domain)] = first_disposition(domain)
    (OUT/'independent_audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
