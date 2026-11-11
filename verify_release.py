"""Check release hashes, run both exact verifiers, compare every JSON field.

Python >=3.10, standard library only. Does not write into the release tree.
Use --checksums-only for a fast integrity check; default performs full verification.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,tempfile,time,zipfile,uuid
from contextlib import contextmanager

ROOT=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(ok,msg):
    if not ok:raise RuntimeError(msg)

@contextmanager
def scratch_directory(base):
    # An inherited-access directory avoids Python 3.13 Windows mode-0700 ACL
    # restrictions on controlled execution tokens. Outputs contain no secrets.
    base=Path(base or tempfile.gettempdir()).resolve()
    p=(base/('core_couple_release_'+uuid.uuid4().hex)).resolve()
    require(p.is_relative_to(base),'Unsafe scratch path')
    p.mkdir(mode=0o755)
    try:yield p
    finally:
        # Only our own two output files are removed; no recursive deletion.
        for name in ['gen1_results.json','gen2_results.json']:
            f=p/name
            if f.is_file():f.unlink()
        p.rmdir()

def checksums():
    entries={}
    for line in (ROOT/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        h,name=line.split(maxsplit=1);name=name.lstrip('*')
        p=(ROOT/name).resolve();require(p.is_relative_to(ROOT),'Unsafe manifest path')
        require(name not in entries,'Duplicate manifest path');entries[name]=h
        require(p.is_file() and digest(p)==h,'SHA-256 mismatch: '+name)
    actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt' and '.git' not in p.relative_to(ROOT).parts}
    require(actual==set(entries),'Unexpected or missing release files')
    subset=json.loads((ROOT/'input_snapshot/subset_checksums_v1.json').read_text())
    snapshot=ROOT/'input_snapshot/required_frozen_inputs_v1.zip'
    require(digest(snapshot)==subset['archive_sha256'],'Regression snapshot ZIP digest')
    with zipfile.ZipFile(snapshot) as z:
        require(set(z.namelist())==set(subset['members']),'Snapshot member inventory')
        for name,h in subset['members'].items():require(hashlib.sha256(z.read(name)).hexdigest()==h,'Snapshot member '+name)
    cff=json.loads((ROOT/'CITATION.cff').read_text(encoding='utf-8')) # JSON is valid YAML 1.2.
    require(cff['cff-version']=='1.2.0' and cff['type']=='software' and cff['version']=='2.0.0','CFF required fields')
    require(bool(cff['title']) and bool(cff['message']) and len(cff['authors'])==1,'CFF citation fields')
    json.loads((ROOT/'metadata/zenodo_metadata.json').read_text(encoding='utf-8'))
    return len(entries)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checksums-only',action='store_true')
    parser.add_argument('--work-dir',type=Path,help='Existing writable scratch directory (default: system temporary directory)')
    parser.add_argument('--report',type=Path,help='Optional result JSON outside the release directory')
    args=parser.parse_args()
    result={'status':'FAIL','checks':{},'verification_mode':'checksums_only' if args.checksums_only else 'full'}
    try:
        result['checks']['manifest_files']=checksums()
        result['checks']['SHA256']='PASS'
        if not args.checksums_only:
            with scratch_directory(args.work_dir) as td:
                for g in ['gen1','gen2']:
                    stem='CORE_COUPLE_'+g.upper()+'_exact_'
                    output=Path(td)/(g+'_results.json')
                    command=[sys.executable,'-B',str(ROOT/g/(stem+'falsifier_v1.py')),'--output',str(output)]
                    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
                    start=time.perf_counter()
                    p=subprocess.run(command,cwd=td,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    require(p.returncode==0,g+' verifier failed (exit '+str(p.returncode)+')')
                    expected=ROOT/g/'expected'/(stem+'results_v1.json')
                    semantic=json.loads(output.read_text(encoding='utf-8'))==json.loads(expected.read_text(encoding='utf-8'))
                    byte=output.read_bytes()==expected.read_bytes()
                    require(semantic,g+' SCIENTIFIC_OUTPUT_MISMATCH: parsed JSON differs')
                    result['checks'][g]={'status':'PASS','JSON_SEMANTIC_EQUIVALENCE':'PASS',
                        'BYTE_EQUALITY':'PASS' if byte else 'DIFFERENT_SERIALIZATION',
                        'expected_sha256':digest(expected),'generated_sha256':digest(output),
                        'elapsed_seconds':round(time.perf_counter()-start,3)}
            # Temporary outputs were outside the release; verify manifest again.
            checksums()
        result['status']='PASS'
    except Exception as error:
        result['error']=str(error)
    if args.report:
        require(not args.report.resolve().is_relative_to(ROOT),'Report must be outside release root')
        args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main())
