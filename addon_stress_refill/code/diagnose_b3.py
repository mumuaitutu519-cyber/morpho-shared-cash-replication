"""Exact integer max-flow audit of dates where the aggregate bound differs."""
from collections import deque
import json,numpy as np
from numba import njit
import pandas as pd
from preflight import O
def maximum_payment(g,vg,f):
    vaults=sorted(vg.vault);markets=sorted(g.market.unique());nodes=len(vaults)+len(markets)+2;sink=nodes-1;adj=[[] for _ in range(nodes)]
    vm={v:i+1 for i,v in enumerate(vaults)};mm={m:i+1+len(vaults) for i,m in enumerate(markets)}
    def edge(a,b,c):adj[a].append([b,c,len(adj[b])]);adj[b].append([a,0,len(adj[a])-1])
    total=0
    for r in vg.itertuples():a=int(r.assets)*f//100;edge(0,vm[r.vault],a);total+=a
    for r in g.itertuples():edge(vm[r.vault],mm[r.market],int(r.position))
    for m,h in g.groupby('market'):edge(mm[m],sink,int(h.cash.iloc[0]))
    flow=0
    while True:
        level=[-1]*nodes;level[0]=0;q=deque([0])
        while q:
            a=q.popleft()
            for b,c,_ in adj[a]:
                if c and level[b]<0:level[b]=level[a]+1;q.append(b)
        if level[sink]<0:break
        cursor=[0]*nodes
        def send(a,amount):
            if a==sink:return amount
            while cursor[a]<len(adj[a]):
                e=adj[a][cursor[a]];b,c,rev=e
                if c and level[b]==level[a]+1:
                    sent=send(b,min(c,amount))
                    if sent:e[1]-=sent;adj[b][rev][1]+=sent;return sent
                cursor[a]+=1
            return 0
        while True:
            sent=send(0,total)
            if not sent:break
            flow+=sent
    return flow
@njit(cache=True)
def search(cash,positions,queue,lengths,requests,used,order,depth):
    if depth==len(used):return True
    for v in range(len(used)):
        if used[v]:continue
        current=cash.copy();need=requests[v]
        for j in range(lengths[v]):
            m=queue[v,j];take=min(need,positions[v,m],current[m]);current[m]-=take;need-=take
            if need==0:break
        if need:continue
        used[v]=True;order[depth]=v;possible=True
        for other in range(len(used)):
            if used[other]:continue
            capacity=0
            for j in range(lengths[other]):
                m=queue[other,j];capacity+=min(positions[other,m],current[m])
            if capacity<requests[other]:possible=False;break
        if possible and search(current,positions,queue,lengths,requests,used,order,depth+1):return True
        used[v]=False
    return False
def queue_order(g,vg,f):
    vaults=sorted(vg.vault);markets=sorted(g.market.unique());vm={v:i for i,v in enumerate(vaults)};mm={m:i for i,m in enumerate(markets)}
    cash=np.array([int(g[g.market.eq(m)].cash.iloc[0]) for m in markets],np.int64);pos=np.zeros((10,len(markets)),np.int64);q=np.full((10,32),-1,np.int64);lengths=np.zeros(10,np.int64)
    for r in g.itertuples():i=vm[r.vault];j=mm[r.market];pos[i,j]=r.position;q[i,r.rank]=j;lengths[i]=max(lengths[i],r.rank+1)
    req=vg.set_index('vault').reindex(vaults).assets.to_numpy(np.int64)*f//100;order=np.full(10,-1,np.int64);found=search(cash,pos,q,lengths,req,np.zeros(10,np.bool_),order,0)
    return [vaults[i] for i in order] if found else None
def run():
    p=pd.read_parquet(O/'positions.parquet');v=pd.read_parquet(O/'vault_states.parquet');d=pd.read_csv(O/'B3_daily_checks.csv');rows=[];joint=pd.read_csv(O/'daily.csv').set_index('date').J
    for r in d[d.mismatch].itertuples():
        flow=maximum_payment(p[p.date.eq(r.date)],v[v.date.eq(r.date)],r.f)
        order=queue_order(p[p.date.eq(r.date)],v[v.date.eq(r.date)],r.f) if r.f==25 and flow==r.request_micro else None
        rows.append(dict(date=r.date,f=r.f,request_micro=r.request_micro,J_micro=int(joint.loc[r.date]),fixed_order_paid_micro=r.initial_paid_micro,max_flow_paid_micro=flow,allocation_fully_feasible=flow==r.request_micro,queue_order_feasible=order is not None if r.f==25 else None,feasible_queue_order=json.dumps(order) if order else None,aggregate_bound_not_sufficient=flow<r.request_micro))
    z=pd.DataFrame(rows);z.to_csv(O/'B3_maxflow_diagnosis.csv',index=False);print(z[z.f.eq(25)].to_string(index=False),flush=True)
if __name__=='__main__':run()
