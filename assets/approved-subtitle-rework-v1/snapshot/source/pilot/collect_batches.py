"""Collect actual complete outputs and independent verification; no rendering or stage acceptance."""
from pathlib import Path
import json,hashlib,sys,subprocess,html
P=Path(__file__).resolve().parents[2];sys.path.insert(0,str(P/'source/pilot'))
import batch_runtime as rt
R=P/'reviews/pilot/integration';R.mkdir(exist_ok=True)
def load(p):return json.loads(Path(p).read_text('utf-8-sig'))
def dump(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
NAMES={'pilot':'已认可前两组','prompts':'口播提示与字幕强调','evidence':'证据、文献与人物分层','stages':'多阶段场景与示意'}

def main():
 cat=load(P/'observations/group-catalog.json');occs={x['id']:x for x in cat['occurrences']};rows=[];tech=[]
 approved=load(P/'reviews/pilot/user-approval.json')
 for g in load(P/'render/pilot/manifest.json')['groups']:
  oid=g['occurrence'];a=next(a for a in approved['groups'] if a['occurrence']==oid);assert sha(P/g['file'])==a['mediaSha256'];assert sha(P/'source/pilot/components.py')==a['sourceSha256'];g.update(batch='pilot',status='user-approved-specific-media');g['recipe']=f'source/pilot/{oid}-recipe.json';g['limitations']=['按已展示媒体范围获用户认可；原字体身份、声音听审与通用迁移不由认可自动推导'];rows.append(g)
 for batch in ['prompts','evidence','stages']:
  manifest=load(P/f'render/pilot/batches/{batch}/manifest.json')
  for g in manifest['groups']:
   oid=g['occurrence'];g.update(batch=batch,status='trial-awaiting-user-review')
   assert g.get('recipe'),oid
   r=load(P/g['recipe']);rt.validate(r)
   assert r['occurrence']==oid
   assert sha(P/g['file'])==g['sha256'],oid
   info=rt.load_json_probe(P/g['file']);assert int(info['nb_read_frames'])==g['frameCount'];tech.append({'occurrence':oid,'sha256':g['sha256'],'actualDecodedFrameCount':int(info['nb_read_frames']),'recipeInputsSourceHashesChecked':True,'userApproved':False});rows.append(g)
 assert len(rows)==len(occs)==24 and len({g['occurrence'] for g in rows})==24
 rows.sort(key=lambda x:x['occurrence']);families={kind:{} for kind in ['visual','subtitle']}
 for g in rows:
  o=occs[g['occurrence']];g.update(sourceFrames=[o['startFrame'],o['endFrame']],sourceTimecode=o['timecode'],compositionMode=o['compositionMode'],visualFamily=o['visual'],subtitleFamily=o['subtitle'],members=o['members'])
  for kind in ['visual','subtitle']:
   ids=list(dict.fromkeys(([o[kind]] if o.get(kind) else [])+o.get(kind+'Components',[])))
   g[kind+'Components']=ids
   for fid in ids:
    f=next(f for f in cat['families'][kind] if f['id']==fid);families[kind].setdefault(fid,{'name':f['name'],'occurrences':[]})['occurrences'].append(o['id'])
 dump(P/'render/pilot/all-groups-metadata.json',{'groups':rows,'families':families,'sourceCatalogSha256':sha(P/'observations/group-catalog.json'),'approvedPilot':'reviews/pilot/user-approval.json','stageAccepted':False});dump(R/'technical.json',{'newGroups':tech,'count':len(tech),'approvedPilotHashesPreserved':True,'actualFullDecodeAlsoStoredPerGroup':True})
 esc=lambda x:html.escape(str(x),quote=True)
 page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>新参考 · 全部完整动效组对照</title><style>body{margin:0;background:#111720;color:#e9eff8;font:16px/1.65 "Microsoft YaHei",sans-serif}main{max-width:1160px;margin:auto;padding:28px}h1{font-size:28px}article{background:#192331;border:1px solid #34455e;border-radius:14px;padding:22px;margin:24px 0}h2{font-size:22px}.badges,summary{color:#91c5ff}.players{display:grid;grid-template-columns:1fr 1fr;gap:24px}section{min-width:0}video{display:block;width:100%;height:570px;object-fit:contain;background:#05070a}button,select{font:inherit;padding:9px 16px;background:#263f60;color:white;border:1px solid #6793c8;border-radius:7px;margin:8px 8px 8px 0;cursor:pointer}details{margin:14px 0}a{color:#a9d1ff}#error{color:#ffb89c}nav{display:flex;flex-wrap:wrap;gap:12px}@media(max-width:650px){main{padding:12px}.players{gap:10px}video{height:380px}article{padding:12px}h2{font-size:18px}}</style><main><h1>新参考 · 全部完整动效组对照</h1><p>24个完整组：已认可前两组＋三个工作包的新22组候选，共48个播放器。新片均使用技能默认未剪辑口播，素材/重点按新语义调整；不是原片台词重放。当前03待整体核验，不自动入库。</p><p>左侧原对标默认静音，可单独开声。不同台词时长各按原速度播放；技术检查不代表声音听审或字体身份确认。</p><label>工作包 <select id="batch" onchange="filterCards()"><option value="">全部</option>'''+''.join(f'<option value="{key}">{v}</option>' for key,v in NAMES.items())+'''</select></label><span id="count"></span><p id="error" role="alert"></p><nav>'''+''.join(f'<a href="#{g["occurrence"]}">{g["occurrence"]}</a>' for g in rows)+'''</nav><details><summary>family 复用映射</summary>'''
 for kind,items in families.items():page+='<p>'+esc(kind)+'：'+'；'.join(esc(fid)+' → '+esc(','.join(f['occurrences'])) for fid,f in items.items())+'</p>'
 page+='</details>'
 for g in rows:
  oid=g['occurrence'];state='已认可该媒体' if g['batch']=='pilot' else '新候选待核验';mode={'combined':'画面＋字幕动态组合','visual-only':'仅画面动效','subtitle-only':'仅字幕动效'}[g['compositionMode']]
  page+=f'<article id="{oid}" data-batch="{g["batch"]}"><h2>{oid} · {esc(occs[oid]["name"])}</h2><p class="badges">{mode} · {state}</p><p>画面：{esc(", ".join(g["visualComponents"]) or "无")}　字幕：{esc(", ".join(g["subtitleComponents"]) or "普通主字幕")}<br>原对标 {esc(g["sourceTimecode"])} · 新口播 {g["rawRange"][0]:.3f}–{g["rawRange"][1]:.3f}s</p><div class="players">'
  for path,label in [(g['referenceFile'],'原对标完整组'),(g['file'],'新口播完整结果')]:page+=f'<section><h3>{label}</h3><video controls playsinline preload="metadata" '+('muted ' if label.startswith('原') else '')+f'src="/{esc(path)}?v={sha(P/path)[:12]}"></video></section>'
  limits=g.get('limitations',[])
  page+=f'</div><button onclick="playPair(this)">两条从头播放</button><button onclick="pausePair(this)">暂停</button><details><summary>当前差异、参数与组合配方</summary><ul>'+''.join('<li>'+esc(x)+'</li>' for x in limits)+f'</ul><a href="/{esc(g["input"])}">可编辑输入</a> · <a href="/{esc(g["recipe"])}">引用配方</a></details></article>'
 page+='''<small>实际学习/验证单位是完整occurrence；同family共用实现，变体与当前验证范围分别记录。尚未accept03/04。</small></main><script>async function playPair(b){document.querySelectorAll('video').forEach(v=>v.pause());const vs=[...b.closest('article').querySelectorAll('video')];vs.forEach(v=>v.currentTime=0);try{await Promise.all(vs.map(v=>v.play()));}catch(e){document.querySelector('#error').textContent=e.message}}function pausePair(b){b.closest('article').querySelectorAll('video').forEach(v=>v.pause())}function filterCards(){let n=0;const v=document.querySelector('#batch').value;for(const c of document.querySelectorAll('article')){c.hidden=!!v&&c.dataset.batch!==v;if(!c.hidden)n++;else c.querySelectorAll('video').forEach(v=>v.pause())}document.querySelector('#count').textContent=n+'组'}filterCards();</script></html>'''
 (P/'render/pilot/index.html').write_text(page,'utf-8');print(json.dumps({'completeGroups':24,'newCandidates':22,'players':48},ensure_ascii=False))
if __name__=='__main__':main()
