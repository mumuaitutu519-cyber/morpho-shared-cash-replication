from chain_access import *
import pandas as pd,numpy as np
sys.path.insert(0,str(A.parent/'code/empirical'));from build_panel import build
O=A/'outputs';summ=[];positions=[];vaults=[];contracts=[];checks=[]
def summarize(protocol,chain,day,h,vs,ps,asset,factory,scope):
 p=pd.DataFrame(ps);p=p[p.position_micro>0];S=sum(min(int(v),int(c)) for v,c in zip(p.position_micro,p.cash_micro));J=sum(min(int(g.cash_micro.iloc[0]),sum(int(x) for x in g.position_micro)) for _,g in p.groupby('market'));Q=sum(int(x['assets_micro']) for x in vs);assert 0<=J<=S
 summ.append(dict(protocol=protocol,chain_id=chain,date=day,block=h['block'],block_hash=h['hash'],vaults=len(vs),positive_asset_vaults=sum(v['assets_micro']>0 for v in vs),positive_markets=p.market.nunique(),assets_usdc=Q/1e6,S_usdc=S/1e6,J_usdc=J/1e6,duplicate_usdc=(S-J)/1e6,duplication_rate=(S-J)/S if S else np.nan,S_assets=S/Q if Q else np.nan,J_assets=J/Q if Q else np.nan,asset=asset,status='complete',universe=scope))
 for x in ps:positions.append(dict(protocol=protocol,chain_id=chain,date=day,block=h['block'],block_hash=h['hash'],**x))
 for x in vs:vaults.append(dict(protocol=protocol,chain_id=chain,date=day,block=h['block'],block_hash=h['hash'],**x))
 for role,addresses in [('factory',factory if isinstance(factory,list) else [factory]),('asset',[asset]),('vault',[x['vault'] for x in vs]),('market',p.market.unique())]:
  for ad in addresses:contracts.append(dict(protocol=protocol,chain_id=chain,date=day,block=h['block'],block_hash=h['hash'],role=('market_id' if protocol=='Morpho_V1' and role=='market' else role),address=ad))
for f in sorted((A/'raw').glob('euler_????-??-??.json')):
 z=json.loads(f.read_text());vs=[{'vault':v['address'],'assets_micro':v['totalAssets']} for v in z['vaults']];ps=[{'vault':p['vault'],'market':p['market'],'position_micro':p['position'],'cash_micro':z['markets'][p['market']]['cash']} for p in z['positions']];assert all(x['cash_micro'] is not None for x in ps)
 for v in z['vaults']:
  total=sum(x['position_micro'] for x in ps if x['vault']==v['address']);expected=total+max(v['lostAssets'],v['lastTotalAssets']-total);assert expected==v['totalAssets'],(f,v['address'],expected,v['totalAssets'])
 summarize('Euler_Earn',1,z['day'],z['header'],vs,ps,z['usdc'],z['factory'],'canonical factory complete list at each block')
for f in sorted((A/'raw').glob('morpho_*_????-??-??.json')):
 z=json.loads(f.read_text());chain=z['header']['chain'];audit=json.loads((A/'raw'/f'morpho_factory_audit_{chain}.json').read_text());assert not audit['missing_from_api'] and not audit['not_in_factory_logs'];p,v=build(z);ps=[{'vault':x['vault'],'market':x['market'],'position_micro':x['position'],'cash_micro':x['market_cash'],'core_contract':{137:'0x1bf0c2541f820e775182832f06c0b7fc27a25f67',42161:'0x6c247b1f6182318877311737bac0844baa518f5e'}[chain]} for x in p];vs=[{'vault':x['vault'],'assets_micro':x['assets']} for x in v];assert all(x['asset_reconciliation_gap']==0 for x in v)
 summarize('Morpho_V1',chain,z['name'][-10:],z['header'],vs,ps,z['asset'],z['factory'],'all native-USDC factory deployments; creation at/before state')
 contracts.append(dict(protocol='Morpho_V1',chain_id=chain,date=z['name'][-10:],block=z['header']['block'],block_hash=z['header']['hash'],role='core',address={137:'0x1bf0c2541f820e775182832f06c0b7fc27a25f67',42161:'0x6c247b1f6182318877311737bac0844baa518f5e'}[chain]))
 checks.append({'protocol':'Morpho_V1','chain_id':chain,'day':z['name'][-10:],'reconciled_vaults':len(v)})
# Yearn allocator positions use native current_debt accounting; cash is read from the actual token-holding contract.
for f in sorted((A/'raw').glob('yearn_cash_137_????-??-??.json')):
 z=json.loads(f.read_text());h=z['header'];day=f.name[-15:-5];src=json.loads((A/'raw'/f'yearn_137_{day}.json').read_text());vs=[{'vault':v['address'],'assets_micro':v['totalAssets']} for v in z['vaults']];ps=[];external=set()
 for v in z['vaults']:
  assert v['totalAssets']==v['totalIdle']+v['totalDebt'] and v['totalIdle']<=v['token_cash_micro']
  ps.append({'vault':v['address'],'market':v['address'],'position_micro':v['totalIdle'],'cash_micro':v['totalIdle'],'cash_kind':'vault_idle'})
 for p0 in z['positions']:
  p0=dict(p0);assert p0['claim_micro']>=p0['current_debt'],p0
  if p0['strategy'] in z['unsupported_strategies']:
   fluid=json.loads((A/'raw'/f'fluid_mapping_137_{day}.json').read_text());assert fluid['strategy']==p0['strategy'] and fluid['strategy_idle_micro']==0 and fluid['strategy_fToken_claim_micro']>=p0['claim_micro'];market=fluid['liquidity'];cash=fluid['liquidity_cash_micro']
   for role,ad in [('fToken',fluid['fToken']),('strategy',fluid['strategy']),('liquidity',fluid['liquidity'])]:contracts.append(dict(protocol='Yearn_V3',chain_id=137,date=day,block=h['block'],block_hash=h['hash'],role=role,address=ad))
  else:market=p0['strategy'];cash=p0['cash_micro']
  external.add(market);ps.append({'vault':p0['vault'],'market':market,'position_micro':p0['current_debt'],'cash_micro':cash,'cash_kind':'strategy_underlying','strategy':p0['strategy'],'convertible_claim_micro':p0['claim_micro']})
 summarize('Yearn_V3',137,day,h,vs,ps,z['asset'],sorted({l['address'] for l in src['factory_deployments']}),'documented release factories; native current_debt positions; own idle cash unique')
 summ[-1]['positive_markets']=len(external)
 checks.append({'protocol':'Yearn_V3','chain_id':137,'day':day,'reconciled_vaults':len(vs),'book_position_covered_by_convertible_claim':True})
# Other inspected combinations are retained in a separate coverage record.
coverage=[]
for chain in [1,42161]:
 z=json.loads((A/'raw'/('yearn_2026-09-29.json' if chain==1 else f'yearn_{chain}_2026-09-29.json')).read_text());coverage.append({'protocol':'Yearn_V3','chain_id':chain,'vaults':len(z['vaults']),'positive_debt_strategies':len(z['strategy_interfaces']),'status':'positions read; full underlying cash adapters not completed; Polygon is the reported protocol-chain combination'})
pd.DataFrame(coverage).to_csv(O/'additional_chain_coverage.csv',index=False)
pd.DataFrame(summ).to_csv(O/'cross_protocol_summary.csv',index=False,float_format='%.17g');pd.DataFrame(positions).to_csv(O/'cross_protocol_positions.csv',index=False);pd.DataFrame(vaults).to_csv(O/'cross_protocol_vaults.csv',index=False);pd.DataFrame(contracts).drop_duplicates().to_csv(O/'cross_protocol_contracts.csv',index=False);(O/'cross_protocol_checks.json').write_text(json.dumps(checks,indent=2));print(pd.DataFrame(summ).drop(columns=['universe','asset','block_hash']).to_string(index=False))
