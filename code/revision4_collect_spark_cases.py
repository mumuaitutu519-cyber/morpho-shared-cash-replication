"""Full logs for all existing verified arrivals to historically registered Spark proxies."""
import gzip,hashlib,json,re,urllib.parse,urllib.request
from pathlib import Path
import pandas as pd
from fetch_ethereum_full import get_json,post_sqd,utc_now,SSL_CONTEXT
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'data/raw/revision4/spark_cases';OUT=ROOT/'reports/revision4'
NAMES={2:'Optimism',3:'Arbitrum',6:'Base',10:'Unichain'}
REG=json.loads((ROOT/'config/destination_registry_revision3.json').read_text())

def registry():
    result={}
    for d,n in {0:'Ethereum',**NAMES}.items():
        s=(ROOT/f'data/raw/revision4/spark_registry/{n}.sol').read_text()
        result[d]={k:a.lower() for k,a in re.findall(r'address\s+internal\s+constant\s+(\w+)\s*=\s*(0x[0-9a-fA-F]{40})',s)}
    return result

def main():
    RAW.mkdir(parents=True,exist_ok=True);reg=registry();x=pd.read_csv(OUT/'post_mint_activity_events.csv')
    select=x.apply(lambda r:int(r.domain) in NAMES and r.mint_recipient=='0x'+reg[int(r.domain)]['ALM_PROXY'][2:].rjust(64,'0'),axis=1)
    cases=x[select].copy();cases.to_csv(OUT/'spark_sample_events.csv',index=False)
    records=[]
    for r in cases.drop_duplicates(['domain','destination_block']).itertuples():
        domain=int(r.domain);number=int(r.destination_block);path=RAW/f'domain_{domain}_block_{number}.json.gz'
        if not path.exists():
            query={'type':'evm','fromBlock':number,'toBlock':number,'fields':{'block':{'number':True,'timestamp':True},
                'log':{'address':True,'topics':True,'data':True,'transactionHash':True,'logIndex':True}},'logs':[{}]}
            endpoint=f"https://portal.sqd.dev/datasets/{REG[str(domain)]['dataset']}/stream"
            logs=[json.loads(b) for b in post_sqd(endpoint,query,attempts=6).splitlines() if b.strip()]
            assert logs and all(int(b['header']['number'])==number for b in logs)
            with gzip.open(path,'wt') as f:json.dump({'queried_at':utc_now(),'endpoint':endpoint,'query':query,'records':logs},f)
        records.append({'domain':domain,'block':number,'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        print(domain,number,flush=True)
    # Public signature lookup is independently constrained to the exact known ABI string.
    for sig in ['Deposit(address,address,uint256,uint256)','Deposit(address,address,address,uint256,uint256)','Supply(bytes32,address,address,uint256,uint256)']:
        url='https://www.4byte.directory/api/v1/event-signatures/?'+urllib.parse.urlencode({'text_signature':sig})
        obj=get_json(url,attempts=3)
        matches=[r for r in obj['results'] if r['text_signature']==sig]
        assert len(matches)==1
        records.append({'signature':sig,'topic':matches[0]['hex_signature'],'lookup_url':url})
    # Pin the PSM interface to a pre-cutoff official source snapshot.
    url='https://api.github.com/repos/sparkdotfi/spark-psm/commits?until=2025-11-30T23%3A59%3A59Z&per_page=1'
    commits=get_json(url,attempts=3);sha=commits[0]['sha']
    for name in ['src/interfaces/IPSM3.sol','src/PSM3.sol','README.md']:
        u=f'https://raw.githubusercontent.com/sparkdotfi/spark-psm/{sha}/{name}'
        with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'ghost-redemptions-research/1.0'}),timeout=60,context=SSL_CONTEXT) as f:b=f.read()
        p=RAW/Path(name).name;p.write_bytes(b)
        records.append({'source_url':u,'file':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest()})
    morpho_commits=get_json('https://api.github.com/repos/morpho-org/morpho-blue/commits?until=2025-11-30T23%3A59%3A59Z&per_page=1',attempts=3)
    morpho_sha=morpho_commits[0]['sha']
    for name in ['src/libraries/EventsLib.sol','src/Morpho.sol']:
        u=f'https://raw.githubusercontent.com/morpho-org/morpho-blue/{morpho_sha}/{name}'
        with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'ghost-redemptions-research/1.0'}),timeout=60,context=SSL_CONTEXT) as f:b=f.read()
        p=RAW/Path(name).name;p.write_bytes(b)
        records.append({'source_url':u,'file':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest()})
    (OUT/'spark_case_manifest.json').write_text(json.dumps({'created_at':utc_now(),'sample_events':len(cases),'items':records},indent=2)+'\n')

if __name__=='__main__':main()
