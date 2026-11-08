import json
import pandas as pd
from hourly import batches,sel,word,ref,A,R,H
def decode_text(words):
    if words is None:return None
    b=b''.join(int(w).to_bytes(32,'big') for w in words)
    if len(b)==32:return b.rstrip(b'\0').decode(errors='replace')
    offset=int.from_bytes(b[:32],'big');n=int.from_bytes(b[offset:offset+32],'big')
    return b[offset+32:offset+32+n].decode(errors='replace')
def run():
    rows=[]
    for chain in [1,42161]:
        f=R/(f'additional_evidence/cross_chain/raw/morpho_{chain}_2025-11-30.json' if chain==1 else 'additional_evidence/raw/morpho_42161_2025-11-30.json')
        z=json.loads(f.read_text());tokens=sorted({'0x'+word(m['params'][1])[-40:] for m in z['market'].values() if m['params'][1]})
        universe=set(tokens)
        for path in H.glob(f'{chain}_*.json'):
            universe.update('0x'+word(m['params'][1])[-40:] for m in json.loads(path.read_text())['market'].values() if m['params'][1])
        tokens=sorted(universe)
        vals=batches(chain,[(z['block'],[(a,sel(fn)) for a in tokens for fn in ['symbol()','name()']])])[0]
        for i,a in enumerate(tokens):
            assert vals[2*i] is not None and vals[2*i+1] is not None,('token metadata read failed',chain,a)
            rows.append(dict(chain=chain,address=a,symbol=decode_text(vals[2*i]),name=decode_text(vals[2*i+1]),metadata_block=z['block']))
    d=pd.DataFrame(rows);d.to_csv(A/'out/collateral_symbols.csv',index=False)
    review=d[d.name.fillna('').str.contains('Elixir|Stream',case=False)|d.symbol.fillna('').str.contains('xUSD|deUSD',case=False)].copy();review['included_main']=review.symbol.isin(['xUSD','deUSD','sdeUSD'])|review.symbol.str.startswith(('PT-sw-xUSD','PT-sdeUSD'));review['review_basis']=review.included_main.map({True:'Exact core symbol or explicitly named principal-token derivative',False:'FalconX, RockawayX or frxUSD name; unrelated to the requested token list'});review.to_csv(A/'out/A3_token_manual_review.csv',index=False)
    checks=[]
    for chain in [1,42161]:
        pre=json.loads((H/f'{chain}_1762127999.json').read_text());g=review[review.chain.eq(chain)&review.included_main];vals=batches(chain,[(pre['block'],[(a,sel(fn)) for a in g.address for fn in ['symbol()','name()']])])[0]
        for i,row in enumerate(g.itertuples()):
            symbol=decode_text(vals[2*i]);name=decode_text(vals[2*i+1]);checks.append(dict(chain=chain,address=row.address,pre_block=pre['block'],pre_symbol=symbol,pre_name=name,metadata_symbol=row.symbol,metadata_name=row.name,symbol_matches=symbol==row.symbol,name_matches=name==row.name))
    check=pd.DataFrame(checks);check.to_csv(A/'out/A3_symbol_time_checks.csv',index=False);assert check.symbol_matches.all() and check.name_matches.all(),'Collateral metadata differs at the pre-W2 block; review required'
    print(d[d.symbol.fillna('').str.contains('USD|usd|Stream|Elixir')].to_string(index=False),flush=True)
if __name__=='__main__':run()
