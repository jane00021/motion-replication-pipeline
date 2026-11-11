"""Review-only collection of the nine authorized reworks plus frozen approved media."""
from pathlib import Path
import json,hashlib,subprocess,sys,copy,html
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[2];sys.path.insert(0,str(P/'source/pilot'))
from components.runtime import validate_recipe,compose,layers,component_source
from components.pairing import check
R=P/'reviews/detail-rest/integration';R.mkdir(parents=True,exist_ok=True)
EXPECTED={'cg07','cg08','cg09','cg10','cg11','cg12','cg14','cg15','cg16'}
def load(p):return json.loads(Path(p).read_text('utf-8-sig'))
def dump(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return Path(p).relative_to(P).as_posix() if Path(p).is_absolute() else str(p).replace('\\','/')
def main():
 cat={o['id']:o for o in load(P/'observations/group-catalog.json')['occurrences']};rows=[];qa=[];families={};src=load(P/'source/pilot/new-input/manifest.json')['path']
 for batch in ['scene','circle']:
  path=P/f'render/pilot/detail-rest/{batch}/manifest.json'
  for g in load(path)['groups']:
   oid=g['occurrence'];assert oid in EXPECTED
   for key in ['file','referenceFile','recipe','input']:g[key]=rel(g[key]);assert (P/g[key]).is_file()
   g['sha256']=sha(P/g['file']);g.update(batch=batch,sourceRange=[cat[oid]['startFrame'],cat[oid]['endFrame']],sourceTimecode=cat[oid]['timecode'],compositionMode=cat[oid]['compositionMode'],variantMembers=cat[oid]['members'],verificationState='trial-awaiting-user-review')
   recipe=load(P/g['recipe']);validate_recipe(recipe);c=load(P/g['input']);check(recipe,c,P)
   for kind,ref in recipe['components'].items():
    if ref['id']:
     key=kind+':'+ref['id'];families.setdefault(key,{'entrypoint':ref['entrypoint'],'source':rel(component_source(kind,ref)),'occurrences':[]});assert families[key]['entrypoint']==ref['entrypoint'];families[key]['occurrences'].append(oid)
   subprocess.run(['ffmpeg','-v','error','-threads','2','-i',str(P/g['file']),'-f','null','-'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
   info=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,width,height','-of','json',str(P/g['file'])]))['streams'][0];N=int(info['nb_read_frames']);assert N==g['frameCount']
   n=N//2;rawp=R/f'{oid}-raw.png';subprocess.run(['ffmpeg','-v','error','-y','-ss',str(g['rawRange'][0]+n/30),'-i',src,'-frames:v','1','-vf','scale=286:508',str(rawp)],check=True)
   raw=Image.open(rawp).convert('RGBA');produced=layers(recipe,raw,n,c);canvas=Image.new('RGBA',(286,508))
   for name in recipe['layerOrder']:
    if name in produced:canvas.alpha_composite(produced[name])
   direct=compose(recipe,raw,n,c);delta=int(np.abs(np.asarray(canvas).astype(int)-np.asarray(direct).astype(int)).max());assert delta==0,(oid,'nondeterministic layer composition',delta)
   bad=copy.deepcopy(recipe);next(iter(bad['components'].values()))['sha256']='0'*64
   try:validate_recipe(bad)
   except ValueError:pass
   else:raise AssertionError('stale source accepted')
   qa.append({'occurrence':oid,'sha256':g['sha256'],'fullVideoAudioDecode':True,'frames':N,'independentLayerRecompositionExact':True,'staleComponentRejected':True,'perceptualApproval':False,'listening':False});rows.append(g)
 assert {g['occurrence'] for g in rows}==EXPECTED
 rows.sort(key=lambda g:g['occurrence']);approval=load(P/'reviews/detail-two/user-approval.json')
 for a in approval['groups']:assert sha(P/a['file'])==a['sha256'],'approved media changed'
 metadata={'stage':'03-pilot','groups':rows,'families':families,'frozenApproved':approval['groups'],'formalLibraryAccepted':False,'userReviewPending':True}
 dump(P/'render/pilot/detail-rest/metadata.json',metadata);dump(R/'technical.json',{'groups':qa,'familyMappings':families,'approvedMediaHashesPreserved':True,'formalLibraryAccepted':False})
 esc=lambda x:html.escape(str(x),quote=True)
 page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>其他组细节返工 · 待核验</title><style>body{background:#111b28;color:#eaf1fa;font:16px/1.7 "Microsoft YaHei";margin:0}main{max-width:1180px;margin:auto;padding:26px}article{padding:22px;background:#1a2737;border:1px solid #3a526d;border-radius:14px;margin:25px 0}.players{display:grid;grid-template-columns:1fr 1fr;gap:24px}video{width:100%;height:600px;background:#030609;object-fit:contain}button,select{padding:10px 16px;margin:10px 12px 10px 0;color:white;background:#26496f;border:1px solid #76a0ce;border-radius:6px;font:inherit}a{color:#96c7ff}h2{font-size:23px}small{color:#bed0e5}details{margin-top:15px}@media(max-width:700px){main{padding:10px}article{padding:12px}video{height:420px}.players{gap:10px}}</style><main><h1>其他组细节返工 · 待你核验</h1><p>本轮9组。每组仅原对标＋新口播完整结果；04、13已认可的视频保持原样，放在页面底部的折叠区。当前仍为03试作，未推进正式库。</p><p>原对标默认静音；两条按各自时长正常播放。新候选不继承04/13的认可，字体身份与声音听审按各组记录。</p><label>筛选 <select id="batch" onchange="filterCards()"><option value="">全部9组</option><option value="scene">场景与素材：07／08／09</option><option value="circle">圆窗与字幕：10／11／12／14／15／16</option></select></label><span id="count"></span>'''
 def players(g):
  oid=g['occurrence'];return f'<div class="players"><section><h3>原对标</h3><video controls playsinline muted preload="metadata" src="/{esc(g["referenceFile"])}"></video></section><section><h3>新口播完整结果</h3><video controls playsinline preload="metadata" src="/{esc(g["file"])}?v={g["sha256"][:12]}"></video></section></div><button onclick="playPair(this)">两条从头播放</button><button onclick="this.closest(\'article\').querySelectorAll(\'video\').forEach(v=>v.pause())">暂停</button>'
 for g in rows:
  oid=g['occurrence'];o=cat[oid];limits=g.get('limitations',[]);page+=f'<article id="{oid}" data-batch="{g["batch"]}"><h2>{oid[2:]} · {esc(o["name"])}</h2><p>画面 {esc(o["visual"] or "无")} × 字幕 {esc(o["subtitle"] or "普通口播字幕")} · 待核验<br>原对标 {esc(o["timecode"])} · 新口播 {g["rawRange"][0]:.3f}–{g["rawRange"][1]:.3f}s</p>'+players(g)+'<details><summary>改动、差异与可编辑入口</summary><ul>'+''.join('<li>'+esc(x)+'</li>' for x in limits)+f'</ul><a href="/{esc(g["input"])}">参数</a> · <a href="/{esc(g["recipe"])}">引用配方</a></details></article>'
 page+='<details id="approved"><summary>查看已认可04／13（原视频保持不动）</summary>'
 for g in load(P/'render/pilot/detail-two/metadata.json')['groups']:page+=f'<article id="approved-{g["occurrence"]}" data-approved="true"><h2>{g["occurrence"][2:]} · 已认可版本</h2>'+players(g)+'</article>'
 page+='''</details><small>当前为源码与配方草案；同family共用实现，occurrence状态独立。未自动accept03/04。</small></main><script>async function playPair(b){document.querySelectorAll('video').forEach(v=>v.pause());const vs=[...b.closest('article').querySelectorAll('video')];vs.forEach(v=>v.currentTime=0);await Promise.all(vs.map(v=>v.play()));}function filterCards(){const selected=document.querySelector('#batch').value;let n=0;for(const a of document.querySelectorAll('article[data-batch]')){a.hidden=!!selected&&a.dataset.batch!==selected;if(!a.hidden)n++;else a.querySelectorAll('video').forEach(v=>v.pause());}document.querySelector('#count').textContent=n+'组';}filterCards();</script></html>'''
 (P/'render/pilot/index.html').write_text(page,'utf-8');print(json.dumps({'newReworks':len(rows),'approvedFrozen':2,'fullDecode':len(qa)}))
if __name__=='__main__':main()
