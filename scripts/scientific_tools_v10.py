"""Replayable typed scientific checks; an engineering demonstration, not learned procedures."""
from pathlib import Path
import argparse,copy,json,sys,time
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'src'))
from invariantcell.io import file_hash,digest,write_json,utc_now
from invariantcell.post_confirmation import validate
from invariantcell.scientific_tools_v10 import ToolCall,run_workflow,verify,explain_decision_change
SOURCE='reports/conformacell/construct_review.json'

def records_from_source():
    source=json.loads((P/SOURCE).read_text());records={}
    for key in ('SASBDB','primary_article'):
        values=source['assay_conditions'][key]
        records[key]={'record_id':key,'kind':'inferred','source_sha256':file_hash(P/SOURCE),
            'source_path':SOURCE,'source_locator':'assay_conditions.'+key,
            'temperature_C':values['temperature_C'],'sodium_phosphate_mM':values['sodium_phosphate_mM'],
            'specimen_id':None,'public_available_at':None}
    return records

def calls():return [ToolCall('compare_field',('SASBDB','primary_article'),f) for f in ('temperature_C','sodium_phosphate_mM','specimen_id')]

def replay(out):
    package=json.loads((out/'demo.json').read_text());records=records_from_source()
    if package['records']!=records:raise ValueError('Saved evidence differs from external source')
    expected=calls()
    if len(package['workflow']['witnesses'])!=len(expected):raise ValueError('Witness count differs')
    checks=[verify(c,call,records,{k:digest(records[k]) for k in call.record_ids}) for c,call in zip(package['workflow']['witnesses'],expected)]
    if package['workflow']!=run_workflow(expected,records):raise ValueError('Workflow conclusion differs')
    before=package['synthetic_revision']['before_records'];after=package['synthetic_revision']['after_records']
    if any(r['kind']!='synthetic' for r in [*before.values(),*after.values()]):raise ValueError('Revision illustration must remain synthetic')
    revision_call=[ToolCall('compare_field',('a','b'),'unit')]
    change=explain_decision_change(run_workflow(revision_call,before),run_workflow(revision_call,after),before,after,'annotation_revision')
    if change!=package['synthetic_revision']['explanation']:raise ValueError('Revision explanation differs')
    return {'status':'REPLAY_PASS','witnesses_checked':len(checks),'source_sha256':file_hash(P/SOURCE),'demo_sha256':file_hash(out/'demo.json'),
            'biological_truth_certified':False,'learned_procedure_transfer_demonstrated':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--replay',action='store_true');p.add_argument('--output',default='runs/post_confirmation_v10/scientific-tool-demo-v1');a=p.parse_args()
    validate(P,'engineering');out=(P/a.output).resolve()
    if not out.is_relative_to(P/'runs/post_confirmation_v10'):raise ValueError('Namespaced output required')
    if a.replay:print(json.dumps(replay(out),indent=2));return
    out.mkdir(parents=True,exist_ok=False);start=time.monotonic();records=records_from_source();workflow=run_workflow(calls(),records)
    before={k:{'record_id':k,'kind':'synthetic','source_sha256':digest('synthetic annotation fixture'),'unit':'count'} for k in ('a','b')}
    after=copy.deepcopy(before);after['b']['unit']='area';revision_call=[ToolCall('compare_field',('a','b'),'unit')]
    change=explain_decision_change(run_workflow(revision_call,before),run_workflow(revision_call,after),before,after,'annotation_revision')
    package={'created_at':utc_now(),'boundary':'post_confirmation_v10','records':records,'workflow':workflow,
        'synthetic_revision':{'before_records':before,'after_records':after,'explanation':change},
        'exposure':'Previously reviewed uPAR publication metadata; development demonstration, not new confirmation',
        'scope':'Original candidate/check/replay interface; no trained planner, biological procedure induction or efficacy evaluation'}
    write_json(P,str((out/'demo.json').relative_to(P)),package,overwrite=False)
    receipt=replay(out);receipt.update(wall_seconds=time.monotonic()-start,code_sha256={x:file_hash(P/x) for x in ('scripts/scientific_tools_v10.py','src/invariantcell/scientific_tools_v10.py')})
    write_json(P,str((out/'receipt.json').relative_to(P)),receipt,overwrite=False);print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
