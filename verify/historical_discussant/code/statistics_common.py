import math
import numpy as np
import pandas as pd
from scipy import stats


def group_codes(values):
    return pd.factorize(values, sort=True)[0]


def sums(values, group):
    result = np.zeros((int(group.max())+1, values.shape[1]))
    np.add.at(result, group, values)
    return result


def cluster_cov(scores, bread, groups, rank):
    n = len(scores)
    def part(g):
        g = group_codes(g)
        G = int(g.max())+1
        if G < 2:
            return np.full_like(bread, np.nan)
        s = sums(scores, g)
        return bread @ (s.T@s) @ bread * G/(G-1)*(n-1)/(n-rank)
    result = part(groups[0])
    if len(groups)==2:
        result += part(groups[1])
        result -= part(pd.MultiIndex.from_arrays(groups))
    return result


def nw_vault_cov(scores, bread, vaults, dates, rank, lags):
    frame = pd.DataFrame(scores)
    frame['vault'] = np.asarray(vaults)
    frame['date'] = pd.to_datetime(np.asarray(dates))
    meat = np.zeros_like(bread)
    for _, g in frame.groupby('vault'):
        g = g.drop(columns='vault').set_index('date').sort_index()
        g = g.reindex(pd.date_range(g.index.min(), g.index.max()), fill_value=0).to_numpy()
        meat += g.T@g
        for lag in range(1, min(lags+1, len(g))):
            cross = g[lag:].T@g[:-lag]
            meat += (1-lag/(lags+1))*(cross+cross.T)
    return bread@meat@bread * len(scores)/(len(scores)-rank)


def auc(y, probability):
    y = np.asarray(y).astype(int)
    n1, n0 = y.sum(), (1-y).sum()
    if not n1 or not n0:
        return np.nan
    ranks = pd.Series(probability).rank(method='average').to_numpy()
    return (ranks[y==1].sum()-n1*(n1+1)/2)/(n1*n0)


def star(p):
    return '***' if p<.01 else '**' if p<.05 else '*' if p<.1 else ''


def cell(coefficient, statistic, p):
    if not np.isfinite(coefficient):
        return 'NE'
    return f'{coefficient:.4f}{star(p)} ({statistic:.2f})' if np.isfinite(statistic) else f'{coefficient:.4f} (NE)'


def markdown(frame):
    def fmt(value):
        if pd.isna(value):return 'NA'
        return str(value).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(frame.columns)+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+'\n'.join('| '+' | '.join(fmt(x) for x in row)+' |' for row in frame.itertuples(index=False,name=None))


def event_fit(data, ycol, terms, fe='event_id', draws=999, seed=20261018):
    """Within-event OLS; market/date CR1; null-imposed market wild-t."""
    needed=[ycol,fe,'market','calendar_date']+terms
    z=data.dropna(subset=needed).copy()
    xy=z[[ycol]+terms].astype(float)
    xy-=xy.groupby(z[fe]).transform('mean')
    y=xy.iloc[:,0].to_numpy()
    X=xy.iloc[:,1:].to_numpy()
    keep=np.linalg.norm(X,axis=0)>1e-10
    terms=[t for t,k in zip(terms,keep) if k]
    X=X[:,keep]
    scale=np.sqrt(np.mean(X*X,axis=0))
    X=X/scale
    assert np.linalg.matrix_rank(X)==len(terms)
    bread=np.linalg.inv(X.T@X)
    beta=bread@X.T@y
    resid=y-X@beta
    rank=z[fe].nunique()+len(terms)
    g=group_codes(z.market)
    G=g.max()+1
    dates=z.calendar_date
    covs={'event_original':cluster_cov(X*resid[:,None],bread,[z[fe]],rank),
          'market':cluster_cov(X*resid[:,None],bread,[z.market],rank),
          'market_date':cluster_cov(X*resid[:,None],bread,[z.market,dates],rank)}
    # Event effects nest in markets, so market wild signs commute with absorption.
    Q=np.zeros((G,len(terms),len(terms)))
    for k in range(G):Q[k]=X[g==k].T@X[g==k]
    signs=np.random.default_rng(seed).choice([-1.,1.],size=(G,draws))
    factor=G/(G-1)*(len(y)-1)/(len(y)-rank)
    wp=[]
    for j in range(len(terms)):
        xr=np.delete(X,j,axis=1)
        restricted=y-xr@np.linalg.lstsq(xr,y,rcond=None)[0]
        score=sums(X*restricted[:,None],g)
        delta=bread@score.T@signs
        influence=signs*(score@bread[:,j])[:,None]-np.einsum('gk,kb->gb',np.einsum('j,gjk->gk',bread[:,j],Q),delta)
        se=np.sqrt(factor*np.sum(influence**2,axis=0))
        if covs['market'][j,j]<=0 or not np.isfinite(se).all() or (se<=0).any():
            wp.append(np.nan)
        else:
            obs=beta[j]/np.sqrt(covs['market'][j,j])
            wp.append((1+int(np.sum(np.abs(delta[j]/se)>=abs(obs)-1e-10)))/(draws+1))
    rows=[]
    for name,cov in covs.items():
        df=z[fe].nunique()-1 if name=='event_original' else min(G,z.calendar_date.nunique())-1 if name=='market_date' else G-1
        for j,term in enumerate(terms):
            se=math.sqrt(cov[j,j])/scale[j] if cov[j,j]>0 else np.nan
            coefficient=beta[j]/scale[j]
            t=coefficient/se
            rows.append(dict(term=term,coefficient=coefficient,se=se,t=t,p=2*stats.t.sf(abs(t),df),
                             covariance=name,wild_p_market=wp[j],N=len(y),events=z[fe].nunique(),
                             market_clusters=G,date_clusters=z.calendar_date.nunique(),
                             within_R2=1-resid@resid/(y@y),rank=rank))
    return pd.DataFrame(rows)
