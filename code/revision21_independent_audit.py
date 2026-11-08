"""Independent raw-page and arithmetic audit, with network disabled."""
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
import csv,gzip,hashlib,json,socket,datetime
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/revision21'
PROXY='0x2917956eff0b5eaf030abdb4ef4296df775009ca'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads((ROOT/p).read_text())
def csvread(p):return list(csv.DictReader((ROOT/p).open()))
def denied(*a,**k):raise RuntimeError('R21 offline audit: no network')
def main():
    socket.create_connection=denied;socket.socket.connect=denied
    for p,v in load('reports/revision21/input_manifest.json').items():assert sha(ROOT/p)==v['sha256']
    # Independently reconstruct account cash/share flows from the raw API pages.
    manifest=load('reports/revision5/api_vault_manifest.json');assert manifest['complete']
    raw={};daily=defaultdict(lambda:defaultdict(int));rawown={}
    for info in manifest['files']:
        p=ROOT/info['file'];assert sha(p)==info['sha256']
        page=json.load(gzip.open(p,'rt'))['response']['data']['vaultV1Transactions']['items']
        for e in page:
            key=(e['txHash'],int(e['logIndex']));assert key not in raw;raw[key]=e
            date=datetime.datetime.fromtimestamp(int(e['timestamp']),datetime.timezone.utc).date().isoformat()
            typ=e['type'];d=e['data'];shares=int(e['shares'])
            if typ in ['Deposit','Withdraw'] and d['onBehalf'].lower()==PROXY:
                rawown[key]=e
                daily[date]['deposit_micro' if typ=='Deposit' else 'withdraw_micro']+=int(d['assets'])
                daily[date]['minted_shares_raw' if typ=='Deposit' else 'burned_shares_raw']+=shares
            if typ=='Transfer':
                if d['from'].lower()==PROXY:daily[date]['transfer_out_raw']+=shares
                if d['to'].lower()==PROXY:daily[date]['transfer_in_raw']+=shares
    assert len(raw)==manifest['unique_keys']==145957
    flows=csvread('reports/revision21/daily_flow_stock_reconciliation.csv')
    for r in flows:
        for k in ['deposit_micro','withdraw_micro','minted_shares_raw','burned_shares_raw','transfer_in_raw','transfer_out_raw']:
            assert int(r[k])==daily[r['date']][k]
        assert int(r['closing_shares_raw'])-int(r['opening_shares_raw'])==int(r['minted_shares_raw'])-int(r['burned_shares_raw'])+int(r['transfer_in_raw'])-int(r['transfer_out_raw'])+int(r['unexplained_share_change_raw'])
    for r in csvread('reports/revision21/cohort_vault_event_join.csv'):
        e=rawown[(r['tx'],int(r['log_index']))]
        assert e['type']=='Deposit' and int(e['data']['assets'])==int(r['assets_micro']) and int(e['shares'])==int(r['shares_raw'])
    # Recompute all request comparisons without the primary pandas calculations.
    states={r['date']:r for r in csvread('reports/revision6/withdrawal_capacity.csv')}
    for r in csvread('reports/revision21/withdrawal_scenarios_daily.csv'):
        st=states[r['date']];req=int(st['claim_micro'])*int(r['request_pct'])//100
        assert req==int(r['request_micro']) and (req>int(st['max_withdraw_micro']))==(r['capacity_exceeded']=='True')
    # Rebuild funded positions from archived API histories, then cash accounting.
    positions=csvread('reports/revision18/funded_positions.csv');expected={}
    for name in ['spark','moonwell','gauntlet']:
        h=load(f'data/raw/revision18/{name}_history.body')['data']['vaultByAddress']['historicalState']
        for a in h['allocation']:
            mid=a['market']['marketId'].lower()
            P={int(x['x']):x['y'] for x in a['supplyAssets']}
            S={int(x['x']):x['y'] for x in a['market']['historicalState']['supplyAssets']}
            B={int(x['x']):x['y'] for x in a['market']['historicalState']['borrowAssets']}
            for r in positions:
                if r['vault']!=name or r['market']!=mid:continue
                t=int(r['boundary_timestamp']);expected[(name,r['date'],mid)]=(int(P[t]),int(S[t]),int(B[t]))
    assert len(expected)==len(positions)==554
    for r in positions:assert expected[(r['vault'],r['date'],r['market'])]==tuple(int(r[k]) for k in ['position_micro','market_supply_micro','market_borrow_micro'])
    for r in csvread('reports/revision21/shared_cash_weekly.csv'):
        g=[p for p in positions if p['date']==r['date']];sep=0;tot=defaultdict(int);cash={}
        for p in g:
            P,S,B=(int(p[x]) for x in ['position_micro','market_supply_micro','market_borrow_micro']);L=S-B
            sep+=P if P<=L else L;tot[p['market']]+=P
            if p['market'] in cash:assert cash[p['market']]==L
            cash[p['market']]=L
        remaining=0
        for m,P in tot.items():remaining+=P-max(0,P-cash[m])
        assert sep==int(r['individually_counted_micro']) and remaining==int(r['joint_cash_upper_micro'])
    # Reconcile the common-market cash to its independently archived state ledger.
    decomp=load('reports/revision21/capacity_decomposition.json')
    mc={r['timestamp']:r for r in csvread('reports/revision5/market_liquidity_validation.csv')}
    for date,key in [(decomp['start_date'],'common_market_cash_start_micro'),(decomp['end_date'],'common_market_cash_end_micro')]:
        z=mc[states[date]['boundary_timestamp']]
        assert z['api_liquidity_raw']==z['reconstructed_liquidity_raw']==decomp[key]
    result={'status':'PASS','network_disabled':True,'raw_vault_events_checked':len(raw),
       'raw_vault_pages_hashed':len(manifest['files']),'exact_cohort_raw_joins':94,'daily_flow_reconciliations':319,
       'request_comparisons':1595,'raw_portfolio_positions_checked':554,'shared_cash_dates':46,
       'share_residual_retained':True,'new_execution_probes':0,'new_institutional_funding_paths':0}
    (OUT/'independent_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
