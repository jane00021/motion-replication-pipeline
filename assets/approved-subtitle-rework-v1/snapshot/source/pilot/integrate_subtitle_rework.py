"""Replace only six rejected trials; preserve approved/untouched media and provenance."""
from pathlib import Path
import json, hashlib, html, sys
P=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(P/'source/pilot'))
import batch_runtime as rt
TARGET={'N07','N13','N17','N21','N22','N24'}
def load(p):return json.loads(p.read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 manifests=list((P/'render/pilot/subtitle-rework').rglob('manifest.json'))
 revised={}
 for path in manifests:
  for g in load(path)['groups']:
   assert g['occurrence'] in TARGET
   assert g['occurrence'] not in revised
   rt.validate(load(P/g['recipe']))
   assert sha(P/g['file'])==g['sha256']
   assert int(rt.load_json_probe(P/g['file'])['nb_read_frames'])==g['frameCount']
   revised[g['occurrence']]=g
 assert set(revised)==TARGET,sorted(set(revised))
 meta_path=P/'render/pilot/all-groups-metadata.json'
 old=load(meta_path)
 history=P/'reviews/pilot/subtitle-rework/before-metadata.json'
 if not history.exists():history.write_text(json.dumps(old,ensure_ascii=False,indent=2),'utf-8')
 original=load(history); rows=[]; checks=[]
 catalog={o['id']:o for o in load(P/'observations/group-catalog.json')['occurrences']}
 for prior in original['groups']:
  oid=prior['occurrence'];g=dict(prior)
  if oid in revised:
   g.update(revised[oid]);g['status']='subtitle-reworked-awaiting-user-review'
   g['supersedes']={'file':prior['file'],'sha256':prior['sha256'],'reason':'user-rejected-subtitle-mechanism'}
  else:assert sha(P/g['file'])==prior['sha256']
  g.setdefault('name',catalog[oid]['name']);rows.append(g);checks.append({'occurrence':oid,'sha256':g['sha256'],'untouched':oid not in TARGET})
 old.update(groups=rows,subtitleRework={'targets':sorted(TARGET),'learning':'reviews/pilot/subtitle-rework/case-learning.json','accepted':False})
 meta_path.write_text(json.dumps(old,ensure_ascii=False,indent=2),'utf-8')
 esc=lambda x:html.escape(str(x),quote=True)
 text='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>完整动效组 · 字幕机制返工</title><style>body{margin:0;background:#111720;color:#e9eff8;font:16px/1.65 "Microsoft YaHei",sans-serif}main{max-width:1160px;margin:auto;padding:28px}article{background:#192331;border:1px solid #34455e;border-radius:14px;padding:22px;margin:24px 0}h2{font-size:22px}.players{display:grid;grid-template-columns:1fr 1fr;gap:24px}section{min-width:0}video{display:block;width:100%;height:570px;object-fit:contain;background:#05070a}button,select{font:inherit;padding:9px 16px;background:#263f60;color:white;border:1px solid #6793c8;border-radius:7px;margin:8px;cursor:pointer}a{color:#a9d1ff}#error{color:#ffb89c}@media(max-width:650px){main{padding:12px}.players{gap:10px}video{height:380px}article{padding:12px}}</style><main><h1>完整动效组 · 字幕机制返工</h1><p>本轮修正 N07、N13、N17、N21、N22、N24，默认显示这六组；其余十八组沿用原视频。每组仅保留原对标与新口播完整结果。03仍待效果审核。</p><p>新旧台词时长不同，各按原速度播放。字体候选和剩余差异保留于参数、过程证据；播放技术检查不等于视觉认可或听审。</p><label>显示 <select id="scope" onchange="filterCards()"><option value="rework">本轮六组</option><option value="all">全部24组</option></select></label><span id="count"></span><p id="error"></p>'''
 for g in rows:
  oid=g['occurrence'];changed=oid in TARGET
  text+=f'<article id="{oid}" data-rework="{str(changed).lower()}"><h2>{oid} · {esc(g["name"])}</h2><p>{"字幕已返工，待你核验" if changed else "沿用原媒体，本轮未改"} · 原对标 {esc(g.get("sourceTimecode",""))} · 新口播 {g["rawRange"][0]:.3f}–{g["rawRange"][1]:.3f}s</p><div class="players">'
  for path,label in [(g['referenceFile'],'原对标完整组'),(g['file'],'新口播完整结果')]:
   text+=f'<section><h3>{label}</h3><video controls playsinline preload="metadata" {"muted" if label.startswith("原") else ""} src="/{esc(path)}?v={sha(P/path)[:12]}"></video></section>'
  text+=f'</div><button onclick="playPair(this)">两条从头播放</button><button onclick="pausePair(this)">暂停</button><details><summary>参数、配方与剩余差异</summary><p>'+esc('；'.join(g.get('limitations',[])))+f'</p><a href="/{esc(g["input"])}">可编辑输入</a> · <a href="/{esc(g["recipe"])}">引用式配方</a></details></article>'
 text+='''</main><script>async function playPair(b){document.querySelectorAll('video').forEach(v=>v.pause());const vs=[...b.closest('article').querySelectorAll('video')];vs.forEach(v=>v.currentTime=0);try{await Promise.all(vs.map(v=>v.play()))}catch(e){document.querySelector('#error').textContent=e.message}}function pausePair(b){b.closest('article').querySelectorAll('video').forEach(v=>v.pause())}function filterCards(){let n=0;const all=document.querySelector('#scope').value==='all';for(const c of document.querySelectorAll('article')){c.hidden=!all&&c.dataset.rework!=='true';if(!c.hidden)n++;else c.querySelectorAll('video').forEach(v=>v.pause())}document.querySelector('#count').textContent=n+'组'}filterCards();</script></html>'''
 (P/'render/pilot/index.html').write_text(text,'utf-8')
 (P/'reviews/pilot/subtitle-rework/integration.json').write_text(json.dumps({'checks':checks,'reworked':sorted(TARGET),'othersPreserved':True,'stageAccepted':False},ensure_ascii=False,indent=2),'utf-8')
 print('Integrated six subtitle reworks; eighteen videos preserved')
if __name__=='__main__':main()
