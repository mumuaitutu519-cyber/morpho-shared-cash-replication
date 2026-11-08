"""Validate the market-supply leg for every Base cohort vault deposit."""
import gzip
import json

import pandas as pd

from revision6_collect_destinations import ROOT, OUT, sha
from revision4_collect_spark_cases import registry
from revision6_destination_operations import signatures, topic
from revision5_collect_liquidity import MARKET
from fetch_ethereum_full import TRANSFER_TOPIC


def analyze():
    validation=json.loads((ROOT/'reports/revision4/validation.json').read_text())
    assert validation['status']=='PASS' and validation['market_creation_matches_api']
    assert validation['market_collateral_nonzero']
    reg=registry()[6];vault=reg['MORPHO_VAULT_SUSDC'];morpho=reg['MORPHO'];usdc=reg['USDC']
    all_signatures=signatures()
    sig=all_signatures['Supply(bytes32,address,address,uint256,uint256)']
    vault_operation_topics={all_signatures['Deposit(address,address,uint256,uint256)'],
                            all_signatures['Withdraw(address,address,address,uint256,uint256)']}
    ops=pd.read_csv(OUT/'domain_6_operations.csv',dtype=str)
    deposits=ops[ops.operation.eq('Vault deposit') & ops.validated_native_transfer.eq('True')]
    manifest=json.loads((OUT/'domain_6_receipts.json').read_text())
    files={r['tx_hash']:r for r in manifest['items']};rows=[]
    for tx, group in deposits.groupby('destination_tx',sort=True):
        item=files[tx];path=ROOT/item['file'];assert sha(path)==item['sha256']
        receipt=json.load(gzip.open(path,'rt'))['response']['result']
        logs=sorted(receipt['logs'],key=lambda x:int(x['logIndex'],16))
        used_supply=set();used_transfer=set()
        for dep in group.sort_values('operation_log',key=lambda s:s.astype(int)).itertuples():
            amount=int(dep.amount_micro_usdc);candidates=[]
            next_operations=[int(x['logIndex'],16) for x in logs if x['address']==vault and x['topics']
                             and x['topics'][0] in vault_operation_topics
                             and int(x['logIndex'],16)>int(dep.operation_log)]
            stop=min(next_operations) if next_operations else float('inf')
            for log in logs:
                idx=int(log['logIndex'],16)
                if log['address']!=morpho or log['topics']!=[sig,MARKET,topic(vault),topic(vault)]:continue
                raw=bytes.fromhex(log['data'][2:]);assert len(raw)==64
                if int.from_bytes(raw[:32])!=amount or int.from_bytes(raw[32:])<=0:continue
                if not int(dep.operation_log)<idx<stop or idx in used_supply:continue
                transfers=[x for x in logs if x['address']==usdc
                           and x['topics']==[TRANSFER_TOPIC,topic(vault),topic(morpho)]
                           and int(x['data'],16)==amount and idx<int(x['logIndex'],16)<stop
                           and int(x['logIndex'],16) not in used_transfer]
                if transfers:
                    candidates.append((idx,min(int(x['logIndex'],16) for x in transfers)))
            chosen=min(candidates) if candidates else None
            if chosen:used_supply.add(chosen[0]);used_transfer.add(chosen[1])
            rows.append({'destination_tx':tx,'deposit_log':int(dep.operation_log),
                         'deposit_native_transfer_log':int(dep.native_transfer_log),
                         'amount_micro':str(amount),'linked_market_supply':chosen is not None,
                         'market_id':MARKET,'supply_log':None if chosen is None else chosen[0],
                         'supply_native_transfer_log':None if chosen is None else chosen[1]})
    fields=['destination_tx','deposit_log','deposit_native_transfer_log','amount_micro',
            'linked_market_supply','market_id','supply_log','supply_native_transfer_log']
    output = pd.DataFrame(rows, columns=fields)
    for field in ['deposit_log', 'deposit_native_transfer_log', 'supply_log', 'supply_native_transfer_log']:
        output[field] = pd.array([row[field] for row in rows], dtype='Int64')
    output.to_csv(OUT/'domain_6_market_links.csv',index=False)
    summary={'vault_deposits':len(rows),'linked_deposits':sum(r['linked_market_supply'] for r in rows),
             'all_deposit_micro':str(sum(int(r['amount_micro']) for r in rows)),
             'linked_deposit_micro':str(sum(int(r['amount_micro']) for r in rows if r['linked_market_supply'])),
             'scope':'Equal-amount ordered deposit and selected-market supply; not marginal borrower drawdown'}
    (OUT/'domain_6_market_links_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':analyze()
