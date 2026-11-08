from pathlib import Path
import json,requests,hashlib,pandas as pd
from revision24_rpc import selector
R=Path(__file__).resolve().parents[1];O=R/'reports/revision27';r=pd.read_csv(O/'ethena_deposit_exit_tests.csv',dtype=str).iloc[0];A='0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c';a=A[2:].zfill(64);error=json.loads(r.execution_response)['error']['data'];assert error[:10]==selector('ERC20InsufficientBalance(address,uint256,uint256)');balance=int(error[74:138],16);need=int(error[138:202],16);assert need-balance==1
q={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'from':A,'to':'0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a','gas':'0x989680','data':selector('withdraw(uint256,address,address)')+f'{int(r.capacity_raw):064x}'+a+a},hex(int(r.block))]};p=O/'raw/ethena_rounding_withdraw.json'
if p.exists():ob=json.loads(p.read_text())
else:
 resp=requests.post('https://base.drpc.org',json=q,timeout=35);ob={'request':q,'response':resp.json(),'sha256':hashlib.sha256(resp.content).hexdigest()};p.write_text(json.dumps(ob,indent=2))
assert len(ob['response']['result'])==66;summary={'original_request_micro':int(r.deposit_raw),'available_claim_micro':int(r.claim_raw),'share_shortfall_raw':need-balance,'capacity_sized_withdrawal_success':True,'liquidity_error':False};(O/'ethena_rounding_check.json').write_text(json.dumps(summary,indent=2));print(summary)
