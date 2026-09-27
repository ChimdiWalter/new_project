"""Finite documentary M2 on NIH validation only; never opens final-internal-test."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['WANDB_MODE']='disabled'
from pathlib import Path
import argparse,json,resource,signal,sys,time
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'src'))
from invariantcell.io import file_hash,utc_now
from invariantcell.decision_m2_v13 import representative_panel,build_panel,fit_calibrator,rank_and_select,evaluate,digest
from invariantcell.nih_revision_v13 import solve
PROTOCOL=P/'data/post_confirmation_v13/decision_m2/protocol.json'
OUTPUT=P/'runs/post_confirmation_v13/decision-m2-documentary-v1'


def read(p):return json.loads(Path(p).read_text())
def write(p,value):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x')as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def check():
    protocol=read(PROTOCOL)
    if protocol['evaluation_split']!='validation' or protocol['final_internal_test_access']is not False:raise ValueError('Forbidden M2 partition')
    for name,sha in protocol['input_sha256'].items():
        if 'final_internal_test'in name:raise ValueError('Final test must not be an M2 input')
        path=P/name
        if path.is_symlink()or not path.resolve().is_relative_to(P)or file_hash(path)!=sha:raise ValueError('Frozen M2 input changed: '+name)
    return protocol


def run():
    protocol=check();OUTPUT.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    try:
        paths=protocol['paths']
        development=representative_panel(read(P/paths['development_corpus']),'development')
        if sorted(q['id']for q in development['queries'])!=protocol['candidate_ids']['development']:raise ValueError('Development candidate IDs changed')
        dev_panel=build_panel(development,'development',solve)
        dev_gold_all=read(P/paths['development_gold']);dev_gold={r['id']:dev_gold_all[r['id']]for r in dev_panel}
        calibrator=fit_calibrator(dev_panel,dev_gold)
        write(OUTPUT/'development_calibration.json',calibrator)
        corpus=representative_panel(read(P/paths['validation_corpus']),'validation')
        if sorted(q['id']for q in corpus['queries'])!=protocol['candidate_ids']['validation']:raise ValueError('Validation candidate IDs changed')
        panel=build_panel(corpus,'validation',solve);selections=rank_and_select(panel,calibrator)
        write(OUTPUT/'native_prediction_panel.json',panel)
        write(OUTPUT/'policy_selections.json',selections)
        commitment={'status':'PREDICTIONS_AND_SELECTIONS_COMMITTED','at':utc_now(),'validation_gold_opened':False,
            'final_internal_test_access':False,'protocol_sha256':file_hash(PROTOCOL),
            'native_prediction_panel_sha256':file_hash(OUTPUT/'native_prediction_panel.json'),
            'policy_selections_sha256':file_hash(OUTPUT/'policy_selections.json'),'calibration_sha256':file_hash(OUTPUT/'development_calibration.json')}
        write(OUTPUT/'commitment.json',commitment)
        # Only this evaluator section can load validation labels, after durable commitments.
        gold_all=read(P/paths['validation_gold']);gold={r['id']:gold_all[r['id']]for r in panel}
        result=evaluate(panel,selections,gold)
        result.update(protocol_sha256=file_hash(PROTOCOL),commitment_sha256=file_hash(OUTPUT/'commitment.json'),
            evaluation_split='validation',final_internal_test_access=False,calibration_evaluation='No validation calibration fit or hyperparameter search')
        write(OUTPUT/'results.json',result)
        write(OUTPUT/'receipt.json',{'status':'COMPLETE','wall_seconds':time.monotonic()-start,'maxrss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'validation_gold_after_commitment':True,'final_internal_test_access':False,'biological_M2_complete':False,'queries':len(panel),
            'validation_gold_records_loaded':len(gold_all),'development_gold_records_loaded':len(dev_gold_all),
            'development_static_calls':len(dev_panel),'development_checker_calls':0,
            'download_bytes':0,'paid_usd':0,'artifact_sha256':{str(x.relative_to(OUTPUT)):file_hash(x)for x in OUTPUT.rglob('*')if x.is_file()}})
    except BaseException as e:
        write(OUTPUT/'failure.json',{'status':'FAILED','error':repr(e),'wall_seconds':time.monotonic()-start,'automatic_retry':False});raise


def main():
    ap=argparse.ArgumentParser(description=__doc__);g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--check',action='store_true');g.add_argument('--run',action='store_true');a=ap.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    def expired(*_):raise TimeoutError('Documentary M2 internal270second cap')
    signal.signal(signal.SIGALRM,expired);signal.alarm(270)
    try:
        if a.check:
            p=check();print(json.dumps({'status':'READY_NO_EMPIRICAL_RUN','pins':len(p['input_sha256']),'final_internal_test_access':False}))
        else:run()
    finally:signal.alarm(0)


if __name__=='__main__':main()
