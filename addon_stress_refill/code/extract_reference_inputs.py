import pandas as pd
from preflight import R,O
def run():
    source=R/'additional_evidence/panel_evidence/outputs'
    v=pd.read_parquet(source/'event_vault_horizons.parquet');v=v[v.event_type.eq('borrow')].dropna(subset=['capacity_million']);counts=v.groupby('pair').horizon.nunique();ids=set(v[v.pair.isin(counts[counts.eq(9)].index)].event_id);events=pd.read_csv(source/'borrow_event_list.csv');events=events[events.event_id.isin(ids)];assert len(events)==834;events.to_csv(O/'input_Table8_834_events.csv',index=False)
    states=pd.read_csv(R/'additional_evidence/cross_chain/outputs/vault_state_panel.csv');states=states[~states.zero_S];assert len(states)==2141;states.to_csv(O/'input_Table4_2141_states.csv',index=False)
if __name__=='__main__':run()
