"""Exact-integer first-departure bounds, with historical balance validation."""
from __future__ import annotations
import argparse
import gzip
import json

import numpy as np
import pandas as pd
from scipy.optimize import linprog

from revision6_collect_destinations import ROOT, RAW, OUT, NETWORKS, cached_request, sha
from revision4_collect_spark_cases import registry
from fetch_ethereum_full import TRANSFER_TOPIC


def topic(a):
    return '0x' + a[2:].rjust(64, '0')


def read_rpc(domain, method, params, name):
    assert method in {'eth_chainId', 'eth_call', 'eth_getLogs'}
    response, path = cached_request(RAW/f'domain_{domain}/balances', name, NETWORKS[domain][1],
        {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    assert 'error' not in response and response.get('result') is not None, response
    return response['result'], path


def movement(log, proxy):
    if log['topics'][1] == log['topics'][2]:
        return 0
    amount = int(log['data'], 16)
    return amount * ((log['topics'][2] == topic(proxy)) - (log['topics'][1] == topic(proxy)))


def extrema(initial, events, maximize):
    focal, alternative, target = 0, initial, 0
    choices = []
    for e in events:
        amount = e['amount']
        if e['kind'] == 'focal_in':
            focal += amount
        elif e['kind'] == 'other_in':
            alternative += amount
        else:
            assert e['kind'] == 'out' and amount <= focal + alternative
            use_focal_first = e['target'] if maximize else not e['target']
            take_focal = min(focal, amount) if use_focal_first else max(0, amount-alternative)
            focal -= take_focal; alternative -= amount-take_focal
            assert focal >= 0 and alternative >= 0
            if e['target']:
                target += take_focal
            choices.append(take_focal)
    return target, focal, choices


def lp_check(initial, events, lower, upper):
    """Independent continuous-flow LP; exact report uses integer greedy bounds."""
    outs = [e for e in events if e['kind'] == 'out']
    if not outs:
        assert lower == upper == 0
        return {'max_error_usdc': 0.0, 'tolerance_usdc': 0.0}
    n = len(outs); balances = []; cumulative_focal = []; cash = initial; fin = 0
    for e in events:
        if e['kind'] == 'focal_in':
            cash += e['amount']; fin += e['amount']
        elif e['kind'] == 'other_in':
            cash += e['amount']
        else:
            cash -= e['amount']; assert cash >= 0
            balances.append(cash); cumulative_focal.append(fin)
    # Cumulative focal departures cannot exceed cumulative focal arrivals;
    # the remaining focal stock cannot exceed the actual total cash balance.
    triangle = np.tril(np.ones((n, n)))
    limits = [(0, e['amount']/1e6) for e in outs]
    objective = np.array([float(e['target']) for e in outs])
    b = np.r_[np.array(cumulative_focal)/1e6,
               (np.array(balances)-np.array(cumulative_focal))/1e6]
    errors = []
    tolerance = 1e-5 + 1e-12 * max(initial, fin, *(e['amount'] for e in events))/1e6
    for sign, target in [(1, lower), (-1, upper)]:
        fit = linprog(sign*objective, A_ub=np.r_[triangle, -triangle], b_ub=b,
                      bounds=limits, method='highs',
                      options={'primal_feasibility_tolerance': 1e-8, 'dual_feasibility_tolerance': 1e-8})
        assert fit.success, fit.message
        error = abs(sign*fit.fun-target/1e6); errors.append(error)
        assert error <= tolerance, (error, tolerance)
    return {'max_error_usdc': max(errors), 'tolerance_usdc': tolerance}


def self_test():
    # Explicit artificial unit fixtures: never exported as research observations.
    fixtures = [
        (0, [{'kind':'focal_in','amount':10}, {'kind':'out','amount':7,'target':True}], (7,7)),
        (10,[{'kind':'focal_in','amount':10}, {'kind':'out','amount':7,'target':True}], (0,7)),
        (5, [{'kind':'focal_in','amount':10}, {'kind':'out','amount':8,'target':False},
             {'kind':'out','amount':7,'target':True}], (2,7)),
        (10,[{'kind':'out','amount':10,'target':True}, {'kind':'focal_in','amount':10}], (0,0)),
    ]
    for initial, events, expected in fixtures:
        lo = extrema(initial, events, False)[0]; hi = extrema(initial, events, True)[0]
        assert (lo, hi) == expected
        lp_check(initial, events, lo, hi)
    print('Integer/LP fixture checks PASS', flush=True)


def collect(domain):
    reg = registry()[domain]; proxy, usdc = reg['ALM_PROXY'], reg['USDC']
    chain, _ = read_rpc(domain, 'eth_chainId', [], 'chain_identity')
    assert int(chain, 16) == NETWORKS[domain][2]
    summary = json.loads((OUT/f'domain_{domain}_operations_summary.json').read_text())
    assert summary['complete_route_discovery']
    frame = pd.read_csv(OUT/f'domain_{domain}_matches.csv', dtype=str)
    frame = frame[frame.status.eq('exact_mint')]
    ops = pd.read_csv(OUT/f'domain_{domain}_operations.csv', dtype=str)
    market_links = (pd.read_csv(OUT/'domain_6_market_links.csv',dtype=str)
                    if domain==6 else None)
    receipts = json.loads((OUT/f'domain_{domain}_receipts.json').read_text())
    files = {x['tx_hash']: x for x in receipts['items']}
    if domain == 6:
        # Prefetch only the same independent reads required by the loop below.
        # No new query, sample selection, batching or synthetic response is used.
        # Unique names prevent concurrent writes to the same cache file.
        from revision6_prefetch import prefetch
        jobs = {}
        for tx in sorted(set(frame.destination_tx)):
            item = files[tx]; path = ROOT/item['file']; assert sha(path) == item['sha256']
            receipt = json.load(gzip.open(path, 'rt'))['response']['result']
            block = int(receipt['blockNumber'], 16)
            name = f'block_{block}_usdc_logs'
            jobs[name] = ('eth_getLogs', [{'fromBlock': hex(block), 'toBlock': hex(block),
                                         'address': usdc, 'topics': [TRANSFER_TOPIC]}], name)
            for at in [block-1, block]:
                name = f'block_{at}_proxy_balance'
                jobs[name] = ('eth_call', [{'to': usdc, 'data': '0x70a08231'+proxy[2:].rjust(64, '0')}, hex(at)], name)
        missing = [job for name,job in jobs.items()
                   if not (RAW/f'domain_{domain}/balances/{name}.json.gz').exists()]
        print('Prefetching unchanged historical reads', len(missing), 'of', len(jobs), flush=True)
        prefetch(missing, lambda job: read_rpc(domain, *job))
    rows = []
    for tx, cohort in frame.groupby('destination_tx', sort=True):
        item = files[tx]; path = ROOT/item['file']; assert sha(path) == item['sha256']
        receipt = json.load(gzip.open(path,'rt'))['response']['result']
        block = int(receipt['blockNumber'],16); block_hash = receipt['blockHash']
        usdc_logs, log_path = read_rpc(domain, 'eth_getLogs', [{'fromBlock':hex(block), 'toBlock':hex(block),
                                      'address':usdc, 'topics':[TRANSFER_TOPIC]}], f'block_{block}_usdc_logs')
        assert isinstance(usdc_logs,list) and usdc_logs
        for log in usdc_logs:
            assert log['address'] == usdc and log['topics'][0] == TRANSFER_TOPIC
            assert len(log['topics']) == 3 and len(log['data']) == 66
            assert int(log['blockNumber'],16) == block and log['blockHash'] == block_hash
            assert not log.get('removed',False)
        indices = [int(x['logIndex'],16) for x in usdc_logs]
        assert len(set(indices)) == len(indices)
        usdc_logs.sort(key=lambda x:int(x['logIndex'],16))
        selected = [x for x in usdc_logs if x['transactionHash'] == tx]
        old = [x for x in receipt['logs'] if x['address'] == usdc and x['topics'][0] == TRANSFER_TOPIC]
        key = lambda x: (int(x['logIndex'],16), tuple(x['topics']), x['data'])
        assert sorted(map(key,selected)) == sorted(map(key,old))
        balances, paths = [], [log_path]
        for b in [block-1,block]:
            value,p = read_rpc(domain,'eth_call',[{'to':usdc,'data':'0x70a08231'+proxy[2:].rjust(64,'0')},hex(b)],f'block_{b}_proxy_balance')
            assert len(value) == 66
            balances.append(int(value,16)); paths.append(p)
        assert balances[1]-balances[0] == sum(movement(x,proxy) for x in usdc_logs), 'Block balance reconciliation failed'
        first = min(int(x['logIndex'],16) for x in receipt['logs'])
        opening = balances[0]+sum(movement(x,proxy) for x in usdc_logs if int(x['logIndex'],16)<first)
        assert opening >= 0
        targets = set(ops.loc[ops.destination_tx.eq(tx) & ops.validated_native_transfer.eq('True')
                      & ops.operation.str.endswith('deposit'), 'native_transfer_log'].astype(int))
        focal = {int(r.mint_log):int(r.amount_micro_usdc) for r in cohort.itertuples()}
        events = []
        for log in selected:
            idx = int(log['logIndex'],16); delta = movement(log,proxy)
            if idx in focal:
                assert delta == focal[idx]
                events.append({'kind':'focal_in','amount':delta,'log_index':idx})
            elif delta > 0:
                events.append({'kind':'other_in','amount':delta,'log_index':idx})
            elif delta < 0:
                events.append({'kind':'out','amount':-delta,'target':idx in targets,'log_index':idx})
        assert targets <= {e['log_index'] for e in events if e['kind']=='out'}
        lo, lo_cash, _ = extrema(opening,events,False)
        hi, hi_cash, _ = extrema(opening,events,True)
        check = lp_check(opening,events,lo,hi)
        operation_bounds = {}
        if domain==6:
            target_sets={}
            for label,operation in [('psm','PSM deposit'),('vault','Vault deposit')]:
                selected_ops=ops[ops.destination_tx.eq(tx) & ops.validated_native_transfer.eq('True')
                                 & ops.operation.eq(operation)]
                target_sets[label]=set(selected_ops.native_transfer_log.astype(int))
            selected_links=market_links[market_links.destination_tx.eq(tx)
                                        & market_links.linked_market_supply.eq('True')]
            target_sets['credit_linked']=set(selected_links.deposit_native_transfer_log.astype(int))
            for label,indices in target_sets.items():
                assert indices <= targets
                selected_events=[{**e,'target':e['log_index'] in indices} if e['kind']=='out' else e
                                 for e in events]
                lower=extrema(opening,selected_events,False)[0]
                upper=extrema(opening,selected_events,True)[0]
                selected_check=lp_check(opening,selected_events,lower,upper)
                operation_bounds[label]={'lower_micro':str(lower),'upper_micro':str(upper),
                                         'lp_validation':selected_check}
        incoming = sum(focal.values()); deposits = sum(e['amount'] for e in events if e['kind']=='out' and e['target'])
        assert 0 <= lo <= hi <= min(incoming,deposits)
        row = {'domain':domain,'destination_tx':tx,'block':block,'block_hash':block_hash,
               'opening_balance_micro':str(opening),'frame_mints':len(focal),'frame_micro':str(incoming),
               'validated_deposit_micro':str(deposits),'lower_micro':str(lo),'upper_micro':str(hi),
               'lower_allocation_retained_focal_micro':str(lo_cash),'upper_allocation_retained_focal_micro':str(hi_cash),
               'lp_validation':check,'events':events,'operation_bounds':operation_bounds,
               'files':[{'file':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in paths]}
        rows.append(row)
        if len(rows)%10==0:
            print('First-disposition states',domain,len(rows),summary['destination_transactions'],flush=True)
    assert len(rows)==summary['destination_transactions']
    result = {'domain':domain,'transactions':len(rows),'complete_matched_transaction_frame':True,
              'frame_burns':sum(r['frame_mints'] for r in rows),
              'frame_micro':str(sum(int(r['frame_micro']) for r in rows)),
              'validated_deposit_micro':str(sum(int(r['validated_deposit_micro']) for r in rows)),
              'lower_micro':str(sum(int(r['lower_micro']) for r in rows)),
              'upper_micro':str(sum(int(r['upper_micro']) for r in rows)),
              'zero_lower_transactions':sum(int(r['lower_micro'])==0 for r in rows),
              'lp_max_error_usdc':max(r['lp_validation']['max_error_usdc'] for r in rows),
              'scope':'Feasible first-disposition interval conditional on observed transaction; no behavioral counterfactual'}
    if domain==6:
        result['operation_bounds']={label:{
            'lower_micro':str(sum(int(r['operation_bounds'][label]['lower_micro']) for r in rows)),
            'upper_micro':str(sum(int(r['operation_bounds'][label]['upper_micro']) for r in rows)),
            'lp_max_error_usdc':max(r['operation_bounds'][label]['lp_validation']['max_error_usdc'] for r in rows)}
            for label in ['psm','vault','credit_linked']}
    (OUT/f'domain_{domain}_first_disposition_manifest.json').write_text(json.dumps({'summary':result,'items':rows},indent=2)+'\n')
    (OUT/f'domain_{domain}_first_disposition_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    pd.DataFrame([{k:v for k,v in r.items() if k not in {'events','files','lp_validation','operation_bounds'}} for r in rows]).to_csv(OUT/f'domain_{domain}_first_disposition.csv',index=False)
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--domain',type=int);p.add_argument('--self-test',action='store_true')
    args=p.parse_args()
    if args.self_test:self_test()
    if args.domain is not None:collect(args.domain)
