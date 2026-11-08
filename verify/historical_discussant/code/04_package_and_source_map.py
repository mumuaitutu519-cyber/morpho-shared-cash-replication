import json,shutil,hashlib,importlib.metadata
from pathlib import Path
import pandas as pd
from settings import OUT,R,PE,MANUSCRIPT


def run():
    B=OUT/'package/table8'
    for name in ['data','code','output']:(B/name).mkdir(parents=True,exist_ok=True)
    files={PE/'event_market_horizons.parquet':'event_market_horizons.parquet',
           PE/'borrow_event_list.csv':'borrow_event_list.csv',PE/'borrow_event_candidates.csv':'borrow_event_candidates.csv',
           OUT/'data/event_boundary_audit.csv':'boundary_audit.csv',
           OUT/'data/qualifying_borrows_tail.csv':'qualifying_borrows_tail.csv',
           OUT/'data/table8_isolated_coverage_certified.csv':'isolated_coverage_certified.csv'}
    manifest=[]
    for path,name in files.items():
        dest=B/'data'/name;shutil.copy2(path,dest)
        manifest.append({'path':'data/'+name,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
    estimates=pd.read_csv(OUT/'tables/table8_reestimated_unrounded.csv')
    expected=estimates[(estimates.column.eq(2)&estimates['sample'].eq('main'))|estimates['sample'].eq('isolated168')].copy()
    expected['sample']=expected['sample'].replace({'main':'column2'})
    path=B/'data/expected_unrounded.csv';expected.to_csv(path,index=False)
    manifest.append({'path':'data/expected_unrounded.csv','bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (B/'input_manifest.json').write_text(json.dumps(manifest,indent=2))
    shutil.copy2(Path(__file__).with_name('table8_portable_reproduce.py'),B/'code/reproduce.py')
    shutil.copy2(Path(__file__).with_name('statistics_common.py'),B/'code/statistics_common.py')
    (B/'requirements.txt').write_text(''.join(n+'=='+importlib.metadata.version(n)+'\n' for n in ['numpy','pandas','scipy','pyarrow']))
    (B/'README.md').write_text('''# Table8 column2 and isolated-event reproduction

Run `pip install -r requirements.txt` and `python code/reproduce.py` from this folder. All paths are relative; inputs are pinned with SHA-256. No RPC is needed. The program reconstructs the complete nine-state outcome samples, then censors post-event follow-up at the next qualifying borrow. Threshold borrows are not restricted to those surviving the24-hour cooldown. Pre/event states are retained, reproducing the manuscript's original 4,335 /5,514 observations. The isolated sample contains80 PanelB events; the complete-duplication PanelA subset has58. Outputs preserve unrounded coefficients, t statistics, market/date clustering and999 restricted market wild-t draws, the full selection table and an event list. Source column2 is old review Table10, now current Table8; old review Table19 is current Table11.

This reproduces the original80-event statement, not an assertion that every event has a fully observed prehistory. The supplied boundary audit identifies two early events without seven prior days. The separately certified list has78 events. The extra tail contains21 qualifying borrows and changes the within72/168h overlap totals from547/668 to548/669. Corrected estimates and old/new comparisons are in the discussant report; the manuscript is unchanged.
''')
    sources={
      '1':['joint_review/outputs/historical_cash_summary.csv','joint_review/code/analyze.py'],
      '2':['enrichment/outputs/cross_chain.csv','enrichment/code/analyze.py'],
      '3':['outputs/empirical/regressions.csv; additional_evidence/outputs/regressions.csv; additional_evidence/panel_evidence/outputs/tasks4_5_numeric.csv','code/empirical/estimate.py; additional_evidence/code/estimate_additions.py; additional_evidence/code/estimate_panel_robustness.py'],
      '4':['additional_evidence/cross_chain/outputs/cross_chain_regressions.csv','additional_evidence/code/estimate_cross_chain.py'],
      '5':['joint_review/outputs/joint_request_summary.csv','joint_review/code/analyze.py'],
      '6':['joint_review/outputs/cross_vault_capacity.csv','joint_review/code/cross_vault_states.py'],
      '7':['additional_evidence/panel_evidence/outputs/task1_numeric.csv','additional_evidence/code/estimate_panel_spillover.py'],
      '8':['tables/table8_reestimated_unrounded.csv; data/table8_regression_samples.parquet','code/02_borrow_events.py; package/table8/code/reproduce.py'],
      '9':['reports/revision29/holder_before_after_states.csv; reports/revision33/state_comparisons.csv','code/revision33_validate.py'],
      '10':['reports/revision21/withdrawal_scenarios.csv; reports/revision21/successful_withdrawal_summary.json; reports/revision27/owner_day_panel.parquet','code/revision21_analyze.py; code/revision27_build_panel.py; code/revision27_estimate.py'],
      '11':['real_consequences/outputs/A1_clean_events.csv; real_consequences/outputs/A1_clean_by_vault.csv','real_consequences/code/clean_a1.py'],
      'A1':['reports/revision24/amount_groups_joint_bounds.csv','replay_r24.py'],
      'B1':['additional_evidence/outputs/cross_protocol_summary.csv; additional_evidence/cross_chain/outputs/vault_state_panel.csv','additional_evidence/code/summarize_cross_protocol.py; additional_evidence/code/estimate_cross_chain.py'],
      'B2':['additional_evidence/panel_evidence/outputs/tasks4_5_numeric.csv','additional_evidence/code/estimate_panel_robustness.py'],
      'C1':['package/full_replay/output/full_replay.csv; addon_package/output/Table_C1_Panel_A.csv; addon_package/output/Table_C1_Panel_B.csv','package/full_replay/code/run_all.py; addon_package/code/01_tables.py']}
    rows=[]
    for table,(source,program) in sources.items():
        rows.append(dict(current_table=table,former_review_table={'8':'10','11':'19'}.get(table,''),
                         result_files=source,reproduction_program=program,
                         root='discussant/project relative' if table in ['8','C1'] else 'Replication_Package relative',
                         numeric_checker='code/04_word_checker.py; tables/word_numeric_checks.csv'))
    pd.DataFrame(rows).to_csv(OUT/'SOURCE_MAP.csv',index=False)
    # Validate each asserted legacy program path rather than silently invent a runnable source.
    audit=[]
    for row in rows:
        for item in row['reproduction_program'].split('; '):
            if item.startswith(('package/','code/02_')):path=OUT/item
            elif item.startswith('addon_package/'):path=OUT.parents[1]/item
            else:path=R/item
            audit.append(dict(current_table=row['current_table'],program=item,exists=path.exists()))
    pd.DataFrame(audit).to_csv(OUT/'logs/source_map_program_audit.csv',index=False)
    print('Table8 portable bundle and current source map saved',flush=True)


if __name__=='__main__':run()
