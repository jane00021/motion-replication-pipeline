"""Independent-directory replay of approved parameters plus cache/mask/text checks."""
from pathlib import Path
import argparse, json, copy, hashlib
import numpy as np
from PIL import Image
from render_subtitle import CASE,ROOT,resolve,validate,combined,render
from subtitle_engine.split_title import split_rgba
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=False);results=[]
 public_manifest=ROOT/'examples/public-inputs-manifest.json'
 if public_manifest.is_file():
  expected=json.loads(public_manifest.read_text('utf-8'))
  for path,digest in expected['files'].items():
   assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
  inputs=ROOT/'examples/inputs'
  verification_scope='public-mock-inputs-and-subtitle-engine'
 else:
  approval=json.loads((CASE/'approval.json').read_text('utf-8'))
  for path,info in approval['files'].items():assert hashlib.sha256((CASE/path).read_bytes()).hexdigest()==info['sha256'],path
  inputs=CASE/'inputs'
  verification_scope='historical-approved-archive'
 for p in sorted(inputs.glob('*.json')):
  c=json.loads(p.read_text('utf-8'));r=render(c,args.output/p.stem);c=resolve(c);n=c['frameCount']-1
  # Render terminal frame, then all earlier frames, then terminal: reveal cache must be immutable.
  end=np.asarray(combined(c,n)).copy()
  for i in range(c['frameCount']):combined(c,i)
  assert np.array_equal(end,np.asarray(combined(c,n)))
  changed=copy.deepcopy(c);m=c['mechanism']
  if m=='split-title':changed['splitSubtitle']['gold']='行动'
  elif m=='bilingual-title':changed['text']['english']='A new meaning'
  elif m=='gold-wave':changed['text']['sentence']='逐步行动'
  elif m=='typed-relay':changed['subtitle']['second'][0]['text']='现在'
  else:changed['subtitle']['conclusion']='现在开始行动'
  assert any(not np.array_equal(np.asarray(combined(c,i)),np.asarray(combined(changed,i))) for i in [n//2,n*3//4,n])
  # Compare actual approved full RGBA sequence when archived path exists in current source project is deliberately avoided.
  results.append({'case':p.stem,'fullDecode':r['fullDecode'],'frameCount':r['frameCount'],'cacheStable':True,'textChangesOutput':True})
 layer=combined(resolve(json.loads((inputs/'N21.json').read_text('utf-8'))),0);a,b=split_rgba(layer,340,0,0);a.alpha_composite(b)
 assert np.array_equal(np.asarray(a),np.asarray(layer)),'Split halves duplicated/dropped pixels'
 result={'boundFileHashesVerified':True,'verificationScope':verification_scope,'cases':results,'splitZeroDisplacementConservesPixels':True,'workingDirectory':str(Path.cwd()),'originalProjectRequired':False,'note':'Technical replay and input interventions only; new references still need measured mechanism/font/timing comparison and user review.'}
 (args.output/'check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
