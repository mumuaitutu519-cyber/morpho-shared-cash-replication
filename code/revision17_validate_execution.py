"""Independent offline audit of historical withdrawal scenarios and raw states."""
from pathlib import Path
import gzip
import hashlib
import json
import socket
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/revision17'
VAULT='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a'
PROXY='0x2917956eff0b5eaf030abdb4ef4296df775009ca'
WITHDRAW='0xb460af94'
LIQUIDITY_ERROR='0x4323a555'


def raw(path):
    data=path.read_bytes(); meta=json.loads(path.with_suffix('.json').read_text())
    assert hashlib.sha256(data).hexdigest()==meta['sha256'] and meta['http_status']==200
    return json.loads(data),meta


def main():
    def offline(*args,**kwargs):raise RuntimeError('Offline R17 audit')
    socket.socket.connect=offline
    from revision6_audit_results import capacity
    old=capacity()
    assert old['status']=='PASS' and old['primary_days']==319
    state=json.loads((OUT/'execution_progress.json').read_text())
    assert state['complete'] and state['completed']==state['planned']==319
    probe=json.loads((OUT/'probe_validation.json').read_text())
    assert probe['status']=='PASS' and probe['calls']==9
    baseline=pd.read_csv(ROOT/'reports/revision6/withdrawal_capacity.csv',dtype=str).iloc[1:]
    assert list(baseline.date)==list(pd.date_range('2025-01-16','2025-11-30').strftime('%Y-%m-%d'))
    baseline=baseline.set_index('date')
    assert len(baseline.index.unique())==319
    assert [r['date'] for r in state['rows']]==list(baseline.index)
    # Independent selector calculation and raw-source declaration check.
    import sys
    sys.path.insert(0,str(ROOT/'.research-deps/crypto'))
    from Crypto.Hash import keccak
    assert WITHDRAW=='0x'+keccak.new(data=b'withdraw(uint256,address,address)',digest_bits=256).digest()[:4].hex()
    assert LIQUIDITY_ERROR=='0x'+keccak.new(data=b'NotEnoughLiquidity()',digest_bits=256).digest()[:4].hex()
    errors=(ROOT/'data/raw/revision17/metamorpho_errors.body').read_text()
    assert 'error NotEnoughLiquidity();' in errors
    rows=[]; files={}
    for r in state['rows']+probe['rows']:
        b=baseline.loc[r['date']]
        path=ROOT/r['source_archive'];response,meta=raw(path)
        files[r['source_archive']]=meta['sha256']
        request=meta['request_body']; assert request['method']=='eth_call'
        args,block=request['params']
        assert int(block,16)==int(b.block) and r['block_hash']==b.block_hash
        assert args['to']==VAULT and args['from']==PROXY and set(args)=={'to','from','data','gas'}
        data=args['data'];assert data[:10]==WITHDRAW and len(data)==202
        payload=bytes.fromhex(data[10:]);amount=int.from_bytes(payload[:32],'big')
        assert payload[32:64]==payload[64:96]==bytes(12)+bytes.fromhex(PROXY[2:])
        expected={'micro':1,'quarter':int(b.claim_micro)//4,'overclaim':int(b.claim_micro)+10**6}[r['scenario']]
        assert amount==expected==int(r['requested_micro'])
        assert r['claim_micro']==b.claim_micro and r['reported_max_withdraw_micro']==b.max_withdraw_micro
        if 'result' in response:
            value=response['result'];assert len(value)==66
            assert 0<int(value,16)<=int(b.treasury_shares)
            status='success'; assert str(int(value,16))==r['burned_shares']
        else:
            error=response['error'];assert error.get('data','').startswith('0x')
            status='liquidity_revert' if error['data']==LIQUIDITY_ERROR else 'other_contract_revert'
        assert status==r['status']
        if r['scenario']=='micro':assert status=='success'
        if r['scenario']=='overclaim':assert status!='success'
        if r in state['rows']:
            rows.append({**r,'request_over_reported_capacity_micro':str(max(0,amount-int(b.max_withdraw_micro))),
                         'capacity_rule_agrees_with_liquidity_revert':
                          (amount>int(b.max_withdraw_micro))==(status=='liquidity_revert')})
    frame=pd.DataFrame(rows).drop_duplicates('date')
    assert len(frame)==319
    assert all(int(r.requested_micro)<=int(r.claim_micro) for r in frame.itertuples())
    frame.to_csv(OUT/'quarter_withdrawal_execution.csv',index=False)
    frame['month']=frame.date.str[:7]
    frame['liquidity_revert']=frame.status.eq('liquidity_revert')
    frame['success']=frame.status.eq('success')
    frame['other_error']=frame.status.eq('other_contract_revert')
    monthly=frame.groupby('month').agg(days=('date','size'),successes=('success','sum'),
                  liquidity_reverts=('liquidity_revert','sum'),other_errors=('other_error','sum'))
    assert monthly.days.sum()==319
    monthly.to_csv(OUT/'quarter_withdrawal_monthly.csv')
    failures=frame[frame.liquidity_revert]
    midpoint=frame.iloc[159]
    result={'status':'PASS','read_only':True,'scenario':'floor(holder_claim_micro/4)',
            'start':'2025-01-16','end_inclusive':'2025-11-30','daily_states':319,
            'successful_scenarios':int(frame.success.sum()),
            'exact_liquidity_reverts':int(frame.liquidity_revert.sum()),
            'other_contract_reverts':int(frame.other_error.sum()),
            'unresolved_provider_errors':0,
            'fraction_of_historical_states_with_liquidity_revert':float(frame.liquidity_revert.mean()),
            'capacity_rule_disagreements':int((~frame.capacity_rule_agrees_with_liquidity_revert).sum()),
            'independent_execution_requests':len(files),'historical_state_validation':old,
            'runtime_code_versions':int(baseline.runtime_code_sha256.nunique()),
            'midpoint_example':{k:str(midpoint[k]) for k in ['date','claim_micro','reported_max_withdraw_micro',
                'requested_micro','status','request_over_reported_capacity_micro']},
            'raw_execution_sha256':files,
            'limits':['Scenario requests are not actual submitted withdrawals or realized runs',
                      'One holder at historical closes, not an estimated probability or causal CCTP effect',
                      'No earlier competing withdrawals, allocator response, replacement supply or borrower response',
                      'Claims combine funding origins; the CCTP cohort is not separately withdrawn',
                      'No bank payout or settlement observation; no incremental credit estimate']}
    (OUT/'execution_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['raw_execution_sha256','historical_state_validation']},indent=2))


if __name__=='__main__':main()
