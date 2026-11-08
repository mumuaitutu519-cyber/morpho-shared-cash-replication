import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));from collect_shared import call
q=call('schema_VaultLiquidity','query{__type(name:"VaultLiquidity"){description fields{name description type{name kind ofType{name kind}}}}}')
print(json.dumps(q,indent=2))
q=call('schema_VaultHistory_full','query{__type(name:"VaultHistory"){fields{name description type{name kind ofType{name kind}}}}}')
print('HISTORYFIELDS',[(x['name'],x['type']) for x in q['__type']['fields']])
