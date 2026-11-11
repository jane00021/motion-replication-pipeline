"""Freeze the six approved trials and install their measured subtitle executors."""
from pathlib import Path
import json, shutil, hashlib, datetime
P=Path(__file__).resolve().parents[2]
K=Path('C:/Users/Administrator/.codex/skills/motion-replication-pipeline')
CASE=K/'assets/approved-subtitle-rework-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text('utf-8-sig'))
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf-8')
def main():
 if CASE.exists():raise ValueError('Approved case is immutable; choose a new version')
 CASE.mkdir(parents=True);engine=K/'scripts/subtitle_engine';engine.mkdir(exist_ok=True)
 files={};fonts={};groups=[]
 def copy(p):
  p=p.resolve()
  if not p.is_file():return
  if p.is_relative_to(P):rel=Path('snapshot')/p.relative_to(P)
  else:rel=Path('fonts')/(sha(p)[:12]+p.suffix.lower());fonts[str(p)]=rel.as_posix()
  d=CASE/rel;d.parent.mkdir(parents=True,exist_ok=True)
  if not d.exists():shutil.copy2(p,d)
  files[rel.as_posix()]={'sha256':sha(d),'bytes':d.stat().st_size}
 def paths(v):
  if isinstance(v,dict):
   for k,x in v.items():
    try:
     if (P/k).is_file():copy(P/k)
    except OSError:pass
    paths(x)
  elif isinstance(v,list):
   for x in v:paths(x)
  elif isinstance(v,str) and len(v)<700 and '\n' not in v:
   try:
    f=P/v
    if f.is_file():copy(f)
   except OSError:pass
 for f in (P/'source/pilot').rglob('*.py'):copy(f)
 for f in [P/'observations/group-catalog.json',P/'render/pilot/all-groups-metadata.json',P/'render/pilot/index.html']:copy(f)
 targets={'N07','N13','N17','N21','N22','N24'}
 meta=load(P/'render/pilot/all-groups-metadata.json')
 configs={}
 for g in meta['groups']:
  if g['occurrence'] not in targets:continue
  assert sha(P/g['file'])==g['sha256']
  recipe=load(P/g['recipe']);config=load(P/g['input']);paths(recipe);paths(config)
  for key in ['file','referenceFile','recipe','input']:copy(P/g[key])
  bindings={ref['source']:sha(P/ref['source']) for ref in recipe['components']}
  for path,digest in recipe.get('supportBindings',{}).items():assert sha(P/path)==digest
  for ref in recipe['components']:assert sha(P/ref['source'])==ref['sha256']
  groups.append({'occurrence':g['occurrence'],'media':g['file'],'mediaSha256':g['sha256'],'reference':g['referenceFile'],'input':g['input'],'inputSha256':sha(P/g['input']),'recipe':g['recipe'],'recipeSha256':sha(P/g['recipe']),'sources':bindings,'supportBindings':recipe.get('supportBindings',{}),'layerOrder':recipe['layerOrder'],'disclosedLimitations':g.get('limitations',[])})
  configs[g['occurrence']]=config
 for root in ['reviews/pilot/subtitle-rework','reviews/subtitle-rework/N07','source/pilot/subtitle-rework']:
  for f in (P/root).rglob('*'):
   if f.is_file() and f.suffix.lower() in ['.json','.jpg','.png','.md']:copy(f)
 # Small executable modules retain the proven implementation, with only import relocation.
 core=(P/'source/pilot/components.py').read_text('utf-8').split('\ndef visual(')[0]
 core=core.replace('P=Path(__file__).resolve().parents[2];W,H=284,504;S=4','W,H=284,504;S=4')
 (engine/'core.py').write_text(core,'utf-8')
 (engine/'__init__.py').write_text('"""Calibrated subtitle execution helpers, not a certified general motion library."""\n','utf-8')
 for src,dest in [('N07/providers.py','split_title.py'),('emphasis/providers.py','emphasis.py'),('closing/provider.py','closing.py')]:
  s=(P/'source/pilot/subtitle-rework'/src).read_text('utf-8')
  s=s.replace('from components import ','from .core import ').replace('import components as base','from . import core as base').replace('import components as shared','from . import core as shared').replace('P=shared.P;W,H=284,504;S=4','W,H=284,504;S=4')
  s=s.replace("primitive=importlib.import_module('subtitle-rework.N07.providers').split_rgba","from .split_title import split_rgba\n  primitive=split_rgba")
  (engine/dest).write_text(s,'utf-8')
 def relocate(v):
  if isinstance(v,dict):return {k:relocate(x) for k,x in v.items()}
  if isinstance(v,list):return [relocate(x) for x in v]
  if isinstance(v,str) and v in fonts:return 'asset:'+fonts[v]
  return v
 for oid,c in configs.items():
  mechanism={'N07':'split-title','N13':'bilingual-title','N17':'gold-wave','N21':'split-line','N22':'diagonal-line','N24':'typed-relay'}[oid]
  fields={'split-title':['splitSubtitle'],'bilingual-title':['text','roles','motion'],'gold-wave':['text','roles','motion'],'split-line':['subtitle'],'diagonal-line':['subtitle'],'typed-relay':['subtitle']}[mechanism]
  clean={key:c[key] for key in fields};clean.update(mechanism=mechanism,canvas=[284,504],fps=30,frameCount=c.get('frameCount',c['frames']),caseOnly=True,originOccurrence=oid)
  dump(CASE/f'inputs/{oid}.json',relocate(clean))
 approval={'version':'subtitle-rework-v1','recordedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'quote':'非常之完美；然后把当前修复好的字幕动效组能力更新到skill','scope':sorted(targets),'approvalScope':'当前六个已展示完整结果的字幕视觉效果认可；不等于原字体身份、精确曲线、听审、其他组或整个03节点通过','groups':groups,'files':files,'fontMap':fonts,'stageAccepted':False,'formalLibraryExpanded':False}
 dump(CASE/'approval.json',approval);dump(P/'reviews/pilot/subtitle-rework/user-approval.json',approval)
 dump(K/'assets/approved-subtitle-rework.json',{'version':approval['version'],'case':'assets/approved-subtitle-rework-v1','approval':'assets/approved-subtitle-rework-v1/approval.json','mechanisms':{k:load(CASE/f'inputs/{k}.json')['mechanism'] for k in configs},'executor':'scripts/render_subtitle.py','originalFontConfirmed':False})
 print(json.dumps({'case':str(CASE),'groups':len(groups),'files':len(files),'fonts':len(set(fonts.values()))},ensure_ascii=False))
if __name__=='__main__':main()
