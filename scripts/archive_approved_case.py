"""Archive exact human-approved media and the actual source/parameter snapshot.
Does not mark a pipeline stage accepted or assert independent portability.
"""
from pathlib import Path
import argparse,json,hashlib,shutil,datetime

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_text('utf-8-sig'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--quote',required=True);a=ap.parse_args();P=a.project.resolve();O=a.output.resolve()
 if O.exists():raise ValueError('Never overwrite an existing approved snapshot')
 m=load(P/'render/pilot/all-groups-metadata.json');cat=load(P/'observations/group-catalog.json');O.mkdir(parents=True);copied={};external={};issues=[]
 def copyfile(p):
  p=Path(p).resolve()
  if not p.is_file():return
  if p.is_relative_to(P):rel=p.relative_to(P)
  else:external[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size};return
  key=rel.as_posix()
  if key in copied:return
  dest=O/'snapshot'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);copied[key]={'sha256':sha(p),'bytes':p.stat().st_size}
 def paths(obj):
  if isinstance(obj,dict):
   for k,v in obj.items():
    if isinstance(k,str) and (P/k).is_file():copyfile(P/k)
    paths(v)
  elif isinstance(obj,list):
   for v in obj:paths(v)
  elif isinstance(obj,str) and len(obj)<1024 and '\n' not in obj:
   try:
    p=Path(obj);p=p if p.is_absolute() else P/p
    if p.is_file():copyfile(p)
    elif p.is_dir() and p.resolve().is_relative_to(P) and any(t in obj.lower() for t in ('matte','rgba')):
     for f in p.rglob('*'):
      if f.is_file():copyfile(f)
   except (OSError,ValueError):pass
 for f in (P/'source/pilot').rglob('*.py'):copyfile(f)
 for f in ['render/pilot/all-groups-metadata.json','observations/group-catalog.json','render/pilot/index.html','workflow-context.json','source/pilot/complete01-02/shared-text-style.json']:copyfile(P/f)
 groups=[]
 for g in m['groups']:
  media=P/g['file'];assert sha(media)==g['sha256'],g['occurrence']
  recipe=load(P/g['recipe']);inputs=load(P/g['input']);paths(recipe);paths(inputs)
  for key in ['file','referenceFile','recipe','input']:copyfile(P/g[key])
  bindings=[]
  for kind,ref in recipe['components'].items():
   source=ref.get('source','source/pilot/'+ref['entrypoint'].split(':')[0].replace('.','/')+'.py');actual=sha(P/source);bindings.append({'kind':kind,'family':ref['id'],'source':source,'actualSha256':actual,'recipeSha256':ref['sha256'],'recipeBindingMatches':actual==ref['sha256']})
  stale=[x for x in bindings if not x['recipeBindingMatches']]
  for dep,declared in recipe.get('supportBindings',{}).items():
   p=P/dep
   if p.is_file() and sha(p)!=declared:issues.append({'occurrence':g['occurrence'],'dependency':dep,'issue':'historical technical binding stale; snapshot records actual current bytes, not claimed render provenance'})
  if stale:issues.append({'occurrence':g['occurrence'],'issue':'component source changed since encoded media; approval binds media, current source snapshot needs reproduction check','bindings':stale})
  groups.append({'occurrence':g['occurrence'],'name':g['name'],'sourceFrames':g['sourceRange'],'rawRange':g['rawRange'],'video':g['file'],'videoSha256':g['sha256'],'recipe':g['recipe'],'recipeSha256':sha(P/g['recipe']),'parameters':g['input'],'parametersSha256':sha(P/g['input']),'components':bindings,'compositionOrder':recipe['layerOrder'],'status':'human-approved-displayed-media','disclosedLimitations':g['limitations']})
 record={'schema':1,'createdAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'humanQuote':a.quote,'catalogCompleteOccurrences':len(groups),'legacyMemberCount':len({x for o in cat['occurrences'] for x in o['members']}),'countExplanation':'User calls19 by historical IDs; final merged catalogue contains17 complete occurrences. No additional groups invented.','groups':groups,'files':copied,'externalDependencies':external,'bindingIssues':issues,'approvalScope':'All displayed current visual results approved; original-font identity, full audio audit, arbitrary new-input fidelity and formal stage acceptance are not inferred.','stageAccepted':False,'formalLibraryExpanded':False,'portability':'Source and parameter evidence snapshot; not claimed cleanroom-certified library'}
 (O/'approval.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf-8');print(json.dumps({'groups':len(groups),'files':len(copied),'external':len(external),'historicalBindingIssues':len(issues),'output':str(O)},ensure_ascii=False))
if __name__=='__main__':main()
