"""Collect independently produced 03 trials without changing the frozen decomposition."""
from pathlib import Path
import json,hashlib,html,subprocess,copy,sys
from collections import defaultdict
P=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(P/'source/pilot'))
from components.runtime import compose,layers,validate_recipe,component_source
from components.pairing import check
from PIL import Image
import numpy as np
R=P/'reviews/batches/integration';R.mkdir(parents=True,exist_ok=True)
NAMES={'existing':'已做组 01／02','scene':'场景与素材编排','circle':'圆窗系列','closing':'字幕与收尾'}
def load(p):return json.loads(Path(p).read_text('utf-8'))
def dump(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def relative(p):
 p=Path(p)
 return p.relative_to(P).as_posix() if p.is_absolute() else p.as_posix()
def bind_recipe(path):
 recipe=load(path)
 old=copy.deepcopy(recipe)
 for kind,ref in recipe['components'].items():ref['sha256']=sha(component_source(kind,ref))
 recipe['commonSha256']=sha(P/'source/pilot/components/common.py')
 recipe.setdefault('sharedStyle','source/pilot/complete01-02/shared-text-style.json')
 recipe['sharedStyleSha256']=sha(P/recipe['sharedStyle'])
 support=recipe.setdefault('supportBindings',{})
 for dep in list(support):support[dep]=sha(P/dep)
 for dep in ['source/pilot/components/runtime.py','source/pilot/components/pairing.py']:
  support[dep]=sha(P/dep)
 recipe['completeGroupValidated']=False
 recipe['verificationState']='trial'
 recipe['integrationBinding']='Current dependency snapshot; technical review below does not certify visual matching.'
 if old!=recipe:
  dump(R/(path.stem+'-'+recipe.get('occurrence','')+'-prior-recipe.json'),old)
 dump(path,recipe)
 validate_recipe(recipe)
 return recipe

def collect():
 cat=load(P/'observations/group-catalog.json');occ={o['id']:o for o in cat['occurrences']};rows=[]
 for g in load(P/'render/pilot/complete01-02/manifest.json')['groups']:
  oid='cg'+g['id'];o=occ[oid];i=g['id']
  rows.append(dict(g,occurrence=oid,name=o['name'],batch='existing',recipe=f'source/pilot/complete01-02/recipes/{i}.json',input=f'source/pilot/complete01-02/input-{i}.json',referenceFile=f'observations/accepted-review/{oid}/reference-clip.mp4',visualFamily=o['visual'],subtitleFamily=o['subtitle'],verificationState='trial',limitations=['沿用现有01/02候选；字体、遮挡、动作和声音尚未验收']))
 for batch in ('scene','circle','closing'):
  candidates=[P/f'render/pilot/batches/{batch}/manifest.json',P/f'source/pilot/batches/{batch}/manifest.json',P/f'reviews/batches/{batch}/manifest.json']
  path=next((p for p in candidates if p.exists()),None)
  if not path:raise FileNotFoundError('Batch manifest missing: '+batch)
  for g in load(path)['groups']:
   oid=g.get('occurrence',g.get('id'));o=occ[oid]
   g.update(occurrence=oid,name=o['name'],batch=batch,visualFamily=o['visual'],subtitleFamily=o['subtitle'],sourceRange=[o['startFrame'],o['endFrame']],sourceTimecode=o['timecode'],variantMembers=o['members'],compositionMode=o['compositionMode'])
   g.setdefault('referenceFile',f'observations/accepted-review/{oid}/reference-clip.mp4');g.setdefault('verificationState','trial');g.setdefault('limitations',[])
   rows.append(g)
 assert len(rows)==len(occ)==17
 assert {r['occurrence'] for r in rows}==set(occ)
 for r in rows:
  o=occ[r['occurrence']]
  r.update(sourceTimecode=o['timecode'],variantMembers=o['members'],compositionMode=o['compositionMode'])
  for key in ('file','recipe','input','referenceFile'):
   r[key]=relative(r[key]);assert (P/r[key]).is_file(),r[key]
  r['sha256']=sha(P/r['file'])
 return cat,sorted(rows,key=lambda r:r['occurrence'])

def render_page(metadata):
 esc=lambda s:html.escape(str(s),quote=True)
 def player(path,label):return f'<section><h3>{label}</h3><video controls playsinline preload="metadata" '+('muted ' if label=='原对标' else '')+f'src="/{esc(path)}?v={sha(P/path)[:12]}"></video></section>'
 cards=[]
 for g in metadata['groups']:
  v=g['visualFamily'];t=g['subtitleFamily'];mode={'combined':'画面＋字幕动态组合','subtitle-only':'仅字幕动效','visual-only':'仅画面动效'}[g['compositionMode']]
  vf=metadata['families']['visual'].get(v,{}).get('name','无画面动效');tf=metadata['families']['subtitle'].get(t,{}).get('name','普通口播字幕，不计字幕动效')
  raw=g.get('rawRange',[]);rr='–'.join(f'{x:.3f}s' for x in raw)
  limits=''.join('<li>'+esc(s)+'</li>' for s in g['limitations'])
  cards.append(f'''<article id="{g['occurrence']}" data-batch="{g['batch']}" data-v="{v or ''}" data-t="{t or ''}"><h2>{g['occurrence'][2:]} · {esc(g['name'])}</h2><p class="badges">{mode} · {NAMES[g['batch']]} · 03待复核</p><p>画面：{esc(v or '无')} {esc(vf)}<br>字幕：{esc(t or '无')} {esc(tf)}</p><p>原对标 {esc(g['sourceTimecode'])}（终点帧不含）　新口播 {esc(rr)}<br>时长随新语义调整，两条各按原速度播放。</p><div class="players">{player(g['referenceFile'],'原对标')}{player(g['file'],'新口播完整结果')}</div><div class="buttons"><button onclick="playPair(this)">两条从头播放</button><button onclick="pausePair(this)">暂停</button></div><details><summary>映射与当前差异</summary><p>原始登记：{esc(', '.join(g['variantMembers']))}。引用同一 family 实现；本 occurrence 的时钟、素材与检验状态独立保留。</p><ul>{limits}</ul><a href="/{esc(g['recipe'])}">组合配方</a> · <a href="/{esc(g['input'])}">可编辑输入</a></details></article>''')
 options=''.join(f'<option value="{k}">{v}</option>' for k,v in NAMES.items())
 families=''.join(f'<p>{esc(kind)}：'+ '；'.join(f'{esc(fid)} → {esc(", ".join(f["occurrences"]))}' for fid,f in items.items())+'</p>' for kind,items in metadata['families'].items())
 page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>完整动效组 · 分批复现待复核</title><style>body{margin:0;background:#111720;color:#e9eff8;font:16px/1.65 "Microsoft YaHei",sans-serif}main{max-width:1120px;margin:auto;padding:28px}h1{font-size:28px}article{background:#192331;border:1px solid #34455e;border-radius:14px;padding:22px;margin:24px 0}h2{font-size:22px}.badges,summary{color:#91c5ff}.players{display:grid;grid-template-columns:1fr 1fr;gap:24px}section{min-width:0}video{display:block;width:100%;height:570px;object-fit:contain;background:#05070a}button,select{font:inherit;padding:9px 16px;background:#263f60;color:white;border:1px solid #6793c8;border-radius:7px;margin:8px 8px 8px 0;cursor:pointer}details{margin:14px 0}a{color:#a9d1ff}header{position:relative}#error{color:#ffb89c}@media(max-width:650px){main{padding:12px}.players{gap:10px}video{height:380px}article{padding:12px}h2{font-size:18px}}</style><main><header><h1>完整动效组 · 分批复现</h1><p>17 个完整 occurrence：已有 2 组＋3 个并行工作包的 15 组。每组保留原对标与新口播完整结果。当前为 03 试作待复核，技术检查与用户视觉认可分别记录。</p><p>原对标默认静音，防止双人声重叠；可单独开声。尚未完成声音听审的组不声称声画通过。</p><label>工作包 <select id="batch" onchange="filterCards()"><option value="">全部</option>'''+options+'''</select></label><span id="visible"></span><p id="error" role="alert"></p></header><details><summary>共用 family 与 occurrence 映射</summary>'''+families+'''</details>'''+''.join(cards)+'''<footer>源码与引用式配方草案；正式 04 入库尚未开始。原对标素材不会作为新口播的底片使用。</footer></main><script>async function playPair(b){document.querySelectorAll('video').forEach(v=>v.pause());const vs=b.closest('article').querySelectorAll('video');for(const v of vs)v.currentTime=0;try{await Promise.all([...vs].map(v=>v.play()));}catch(e){document.querySelector('#error').textContent='播放失败：'+e.message;}}function pausePair(b){b.closest('article').querySelectorAll('video').forEach(v=>v.pause())}function filterCards(){let n=0;for(const c of document.querySelectorAll('article')){c.hidden=!!batch.value&&c.dataset.batch!==batch.value;if(!c.hidden)n++;else c.querySelectorAll('video').forEach(v=>v.pause())}document.querySelector('#visible').textContent=n+' 个完整组'}filterCards();</script></html>'''
 (P/'render/pilot/index.html').write_text(page,'utf-8')

def main():
 cat,rows=collect();families={'visual':{},'subtitle':{}}
 for kind in families:
  for f in cat['families'][kind]:
   if any(r[kind+'Family']==f['id'] for r in rows):families[kind][f['id']]={'name':f['name'],'occurrences':[],'implementations':[]}
 checks=[]
 for g in rows:
  recipe=bind_recipe(P/g['recipe']);inputs=load(P/g['input']);check(recipe,inputs,P)
  assert recipe['occurrence']==g['occurrence']
  for kind in ('visual','subtitle'):
   fid=g[kind+'Family']
   if fid:
    ref=recipe['components'][kind];assert ref['id']==fid,(g['occurrence'],kind,ref['id'],fid)
    f=families[kind][fid];f['occurrences'].append(g['occurrence']);entry={'entrypoint':ref['entrypoint'],'source':relative(component_source(kind,ref)),'sha256':ref['sha256']}
    if entry not in f['implementations']:f['implementations'].append(entry)
  # Fully decode all candidate video and audio packets; count frames separately.
  subprocess.run(['ffmpeg','-v','error','-threads','2','-i',str(P/g['file']),'-f','null','-'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=nb_read_frames,width,height','-of','json',str(P/g['file'])]))['streams'][0]
  actual=int(probe['nb_read_frames']);assert actual==g['frameCount'],(g['occurrence'],actual,g['frameCount'])
  # Sample the current recipe and independently recompose its produced slots.
  mid=max(0,actual//2);rawfile=R/(g['occurrence']+'-raw.png')
  rawrange=g['rawRange'];rawpath=load(P/'source/pilot/new-input/manifest.json')['path']
  subprocess.run(['ffmpeg','-v','error','-y','-ss',str(rawrange[0]+mid/30),'-i',rawpath,'-frames:v','1','-vf','scale=286:508',str(rawfile)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  raw=Image.open(rawfile).convert('RGBA');produced=layers(recipe,raw,mid,inputs);combined=Image.new('RGBA',(286,508))
  for name in recipe['layerOrder']:
   if name in produced:combined.alpha_composite(produced[name])
  direct=compose(recipe,raw,mid,inputs)
  assert np.array_equal(np.asarray(combined),np.asarray(direct))
  # Persist actual independent alpha outputs, separate from preview backdrop.
  for name,tile in produced.items():
   if name.startswith('subtitle.'):tile.save(R/(g['occurrence']+'-'+name+'.png'))
  tampered=copy.deepcopy(recipe);next(iter(tampered['components'].values()))['sha256']='0'*64
  try:validate_recipe(tampered)
  except ValueError:pass
  else:raise AssertionError('Stale component accepted')
  checks.append({'occurrence':g['occurrence'],'encodedSha256':g['sha256'],'fullDecode':True,'frameCount':actual,'recipeHashesChecked':True,'independentLayersRecomposeExactly':True,'staleDependencyRejected':True,'observedPairingStructureChecked':True,'visualApproved':False})
 for kind,items in families.items():
  for fid,f in items.items():assert len(f['implementations'])==1,(fid,'multiple family implementations',f)
 metadata={'schema':1,'stage':'03-pilot','status':'trials-awaiting-review','groups':rows,'families':families,'catalogSha256':sha(P/'observations/group-catalog.json'),'rawInput':load(P/'source/pilot/new-input/manifest.json'),'formalLibraryAccepted':False,'verificationDistinction':'fullDecode is a technical check; no inferred perceptual or listening approval'}
 dump(P/'render/pilot/batch-metadata.json',metadata);dump(R/'technical.json',{'groups':checks,'oneImplementationPerFamily':True,'visualFamilies':len(families['visual']),'subtitleFamilies':len(families['subtitle']),'formalLibraryAccepted':False})
 render_page(metadata)
 print(json.dumps({'groups':len(rows),'visualFamilies':len(families['visual']),'subtitleFamilies':len(families['subtitle']),'fullDecode':len(checks)},ensure_ascii=False))
if __name__=='__main__':main()
