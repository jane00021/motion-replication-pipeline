"""Requested shadow revision; only reference + applied A appear in the review entry."""
from pathlib import Path
import json,copy,subprocess
import numpy as np
from PIL import Image,ImageDraw
import t04_render as r
import render_migration as m
P=r.P
def main():
 c=json.loads((r.S/'input-A.json').read_text('utf-8'))
 old=copy.deepcopy(c)
 r.dump(P/'reviews/t04-calibration/A-before-shadow.json',old)
 for role,s in c['roles'].items():
  s['shadow'].update(dx=1.05,dy=1.6,blur=.7,color='#08090d',opacity=.88)
 r.dump(r.S/'input-A.json',c)
 receipt=r.encode(c,r.O/'input-A.mp4')
 r.dump(r.O/'input-A-receipt.json',dict(receipt,sourceSha256=r.file_sha(Path(r.__file__)),inputSha256=r.file_sha(r.S/'input-A.json')))
 raw=m.extract(19.4,3.2);aud=m.audio('t04-shadow',19.4,3.2);frames=[]
 for n,a in enumerate(raw):
  im=Image.fromarray(a).convert('RGBA');im.alpha_composite(r.rgba(c,n).resize((628,1118),Image.Resampling.LANCZOS));frames.append(im.convert('RGB'))
 m.encode(r.O/'applied-A.mp4',frames,aud)
 # Actual rendered ablation at stable body frame, separate from glow.
 n=45;without=copy.deepcopy(c)
 for s in without['roles'].values():s['shadow']['opacity']=0
 a=r.rgba(c,n);b=r.rgba(without,n);changed=int(np.any(np.array(a)!=np.array(b),2).sum());assert changed>0
 out=Image.new('RGB',(628*2,300),'#252a32');d=ImageDraw.Draw(out)
 for j,(cfg,label) in enumerate([(without,'shadow disabled'),(c,'shadow enabled')]):
  im=Image.fromarray(raw[n]).convert('RGBA');im.alpha_composite(r.rgba(cfg,n).resize((628,1118),Image.Resampling.LANCZOS));out.paste(im.crop((0,720,628,1000)),(628*j,20));d.text((628*j+8,3),label,fill='white')
 out.save(P/'reviews/t04-calibration/shadow-ablation.jpg',quality=94)
 page=P/'render/pilot/index.html'
 hist=P/'reviews/t04-calibration/panel-before-simplify.html'
 if not hist.exists():hist.write_text(page.read_text('utf-8'),'utf-8')
 page.write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>字幕动效｜对标与复刻</title>
<style>*{box-sizing:border-box}body{margin:0;background:#10151e;color:#eaf0f8;font:16px/1.7 "Microsoft YaHei",sans-serif}main{max-width:960px;margin:32px auto;padding:0 24px}h1{font-size:25px;margin-bottom:8px}p{color:#aebbd0}.columns{display:grid;grid-template-columns:1fr 1fr;gap:32px}section{background:#192231;border:1px solid #354258;border-radius:12px;padding:20px}h2{font-size:18px;margin:0 0 14px}video{display:block;width:100%;max-width:355px;margin:auto;background:#080b10;border-radius:6px}small{display:block;color:#aebbd0;margin-top:12px}button{font:inherit;padding:8px 16px;border-radius:6px;border:1px solid #5b80b4;background:#29496f;color:white;margin:18px 8px 8px 0;cursor:pointer}@media(max-width:650px){.columns{grid-template-columns:1fr}}</style>
<main><h1>字幕动效 · 对标与新口播复刻</h1><p>已补强文字投影；“天花板”为金色重点，“就在这”为白色辅助。</p><div class="columns"><section><h2>原对标</h2><video controls muted playsinline preload="auto" src="../../observations/accepted-review/cg06/reference-clip.mp4"></video><small>原速度 · 2.2秒</small></section><section><h2>新口播复刻</h2><video controls playsinline preload="auto" src="t04/applied-A.mp4?revision=shadow-v1"></video><small>新台词 · 3.2秒</small></section></div><button id="play">两条从头播放</button><button id="pause">暂停</button><small>两条各自保持原速度，时长不同；可独立拖动。当前仍在03试作复审，尚未验收。</small></main><script>const vs=[...document.querySelectorAll('video')];document.querySelector('#play').onclick=async()=>{for(const v of vs){v.currentTime=0;await v.play();}};document.querySelector('#pause').onclick=()=>vs.forEach(v=>v.pause());</script></html>''','utf-8')
 results=[]
 for path in [r.O/'input-A.mp4',r.O/'applied-A.mp4']:
  d=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True);assert d.returncode==0 and not d.stderr
  results.append({'file':str(path.relative_to(P)),'sha256':r.file_sha(path),'fullDecode':True})
 report=json.loads((P/'reports/03-pilot.json').read_text('utf-8'))
 report['checks'].append({'id':'shadow-and-two-player-review','passed':True,'method':'rendered-shadow-ablation+reencode+full-decode','finding':'正文、辅助词、重点词阴影独立配置并实际渲染；投影在发光峰值保留，不出现矩形底板。当前入口只保留原对标及新口播A。','evidence':['reviews/t04-calibration/shadow-revision.json','reviews/t04-calibration/shadow-ablation.jpg','render/pilot/index.html']})
 r.dump(P/'reports/03-pilot.json',report)
 r.dump(P/'reviews/t04-calibration/shadow-revision.json',{'changedPixels':changed,'shadow':c['roles']['body']['shadow'],'outputs':results,'previousABVerification':'historical r8; A shadow now changed, prior font-only equality receipt is not the current A/B claim','entryPlayers':2,'stageAccepted':False})
 print(json.dumps({'shadowChangedPixels':changed,'players':2}))
if __name__=='__main__':main()
