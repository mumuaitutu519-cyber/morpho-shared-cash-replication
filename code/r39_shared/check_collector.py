"""Failure-path checks use retained responses in isolated temporary directories; no network."""
import collect_public as c
from pathlib import Path
import tempfile,json,csv,threading,contextlib,io
ROOT=c.ROOT;baseline=json.loads(next(c.R.glob('public_liquidity_2026*.json')).read_text());original_request=c.requests.request;original_sleep=c.time.sleep;checks=[]
class Response:
 def __init__(self,status,body):self.status_code=status;self.text=body
 def json(self):return json.loads(self.text)
for scenario in ['first_failure_then_success','both_attempts_fail']:
 with tempfile.TemporaryDirectory(prefix='r39_collector_check_') as tmp:
  c.ROOT=Path(tmp);c.O=c.ROOT/'outputs';c.R=c.ROOT/'raw';c.O.mkdir();c.R.mkdir();calls={};lock=threading.Lock()
  def mock(method,url,json=None,timeout=None):
   label='graphql' if method=='POST' else url.split('8453:')[1].split('/')[0].lower()
   with lock:calls[label]=calls.get(label,0)+1;n=calls[label]
   if label=='graphql' and (scenario=='both_attempts_fail' or n==1):return Response(503,'{"error":"synthetic HTTP failure for retry check"}')
   a=baseline['responses'][label]['attempts'][-1];return Response(a['status'],a['body'])
  c.requests.request=mock;c.time.sleep=lambda x:None
  with contextlib.redirect_stdout(io.StringIO()):c.main();before=calls.copy();c.main()
  assert before==calls and calls['graphql']==2
  files=list(c.R.glob('public_liquidity_*.json'));assert len(files)==1
  rows=list(csv.DictReader((c.O/'public_liquidity_daily.csv').open()));assert len(rows)==1
  assert len(list(csv.DictReader((c.O/'public_liquidity_by_vault.csv').open())))==10
  assert int(rows[0]['failed_attempts'])==(1 if scenario=='first_failure_then_success' else 2)
  if scenario=='both_attempts_fail':assert rows[0]['graphql_public_sum_usdc']=='' and rows[0]['joint_upper_usdc']==''
  raw=json.loads(files[0].read_text());assert len(raw['responses']['graphql']['attempts'])==2
  checks.append({'scenario':scenario,'passed':True,'retry_count':1,'idempotent':True,'no_network':True})
c.requests.request=original_request;c.time.sleep=original_sleep
(ROOT/'outputs/collector_failure_test.json').write_text(json.dumps(checks,indent=2));print('collector retry / missing / idempotence checks passed')
