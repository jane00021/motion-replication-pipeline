from pathlib import Path
import json,sys,subprocess,copy,html
from PIL import Image,ImageDraw,ImageFont
import numpy as np
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'))
from components.common import core,load
from components.runtime import validate_recipe,compose,layers
from components.pairing import check
S=P/'source/pilot/final-two';O=P/'render/pilot/final-two';R=P/'reviews/final-two';font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',12);groups=[];qa=[]
for oid in ['cg17','cg18']:
 c=load(S/f'{oid}-input.json');r=load(S/f'{oid}-recipe.json');validate_recipe(r);check(r,c,P)
 data=subprocess.check_output(['ffmpeg','-v','error','-i',str(O/f'{oid}.mp4'),'-vf','scale=286:508','-f','rawvideo','-pix_fmt','rgb24','pipe:1']);frames=np.frombuffer(data,np.uint8).reshape(-1,508,286,3);N=len(frames);assert N==c['frameCount']
 sheet=Image.new('RGB',(7*292,1060),'#1c2937');d=ImageDraw.Draw(sheet)
 for j,n in enumerate(np.linspace(0,N-1,7,dtype=int)):
  sf=c['sourceRange'][0]+round(n/(N-1)*(c['sourceRange'][1]-c['sourceRange'][0]-1));ref=Image.open(P/'observations/frame-audit/frames'/f'{sf+1:04d}.jpg');sheet.paste(ref,(292*j,25));sheet.paste(Image.fromarray(frames[n]),(292*j,548));d.text((292*j+2,3),f'原f{sf}／新f{n} 阶段对齐',font=font,fill='white')
 sheet.save(R/f'{oid}-encoded-comparison.jpg')
 n=N//2;raw=Image.new('RGBA',(286,508),'#345678');a=layers(r,raw,n,c);re=Image.new('RGBA',(286,508))
 for key in r['layerOrder']:
  if key in a:re.alpha_composite(a[key])
 assert np.array_equal(np.array(re),np.array(compose(r,raw,n,c)))
 for key,tile in a.items():
  if key.startswith('subtitle.'):tile.save(R/f'{oid}-{key}.png')
 changed=copy.deepcopy(c)
 if oid=='cg17':changed['subtitle']['rows'][0]['text']='测试'
 else:changed['subtitle']['phrases'][0]['text']='测一下'
 change=int(np.any(np.array(re)!=np.array(compose(r,raw,n,changed)),2).sum());assert change>0
 if oid=='cg17':
  off=compose(r,raw,n,c,['occlusion']);occlusion=int(np.any(np.array(off)!=np.array(re),2).sum());assert occlusion>0
  diffs=['原字体身份未确认：采用优设标题黑候选，部分字形、斜度与笔画端点仍有差异','RVM透明前景保留人物/手势，细发和运动柔边仍可能有局部误差','原参考1.1秒，新口播2.5秒按语义延长；原独立声效与精确词点尚未听审']
 else:occlusion=None;diffs=['原字体身份未确认；宋体候选及半透明板材质仍有差异','画面恢复满屏按参考关键帧重建，字级时钟按新内容重定时','新口播1.7秒，原参考约1.13秒；音效与逐词听审未通过']
 row={'occurrence':oid,'file':f'render/pilot/final-two/{oid}.mp4','referenceFile':f'observations/accepted-review/{oid}/reference-clip.mp4','recipe':f'source/pilot/final-two/{oid}-recipe.json','input':f'source/pilot/final-two/{oid}-input.json','sourceRange':c['sourceRange'],'rawRange':c['rawRange'],'frameCount':N,'sha256':core.file_sha(O/f'{oid}.mp4'),'purpose':c['purpose'],'limitations':diffs,'status':'trial-awaiting-user-review'};groups.append(row);qa.append({'occurrence':oid,'fullDecode':True,'independentLayerRecompositionExact':True,'changedTextPixels':change,'foregroundOcclusionChangesPixels':occlusion,'largestThree':diffs,'sha256':row['sha256'],'userApproved':False})
core.dump(R/'verification.json',{'groups':qa,'skillAudit':'reviews/final-two/skill-audit.json','perceptualAudioApproval':False,'priorVersionsRetained':True,'stageAccepted':False});core.dump(O/'metadata.json',{'groups':groups,'stage':'03-pilot','accepted':False})
old=P/'render/pilot/index.html';(R/'previous-panel.html').write_text(old.read_text('utf-8'),'utf-8')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>17／18 两组复刻校准</title><style>body{background:#111b28;color:#eaf1fa;font:16px/1.7 "Microsoft YaHei";margin:0}main{max-width:1160px;margin:auto;padding:26px}article{padding:22px;background:#1a2737;border:1px solid #3a526d;border-radius:14px;margin:25px 0}.players{display:grid;grid-template-columns:1fr 1fr;gap:24px}video{width:100%;height:620px;background:#030609;object-fit:contain}button{padding:10px 18px;margin:10px 12px 10px 0;color:white;background:#26496f;border:1px solid #76a0ce;border-radius:6px;font:inherit}a{color:#96c7ff}h2{font-size:23px}details{margin-top:15px}@media(max-width:700px){main{padding:10px}article{padding:12px}video{height:420px}.players{gap:10px}}</style><main><h1>17／18 两组复刻校准 · 待核验</h1><p>这两组已有旧试作，本轮按优化后的校准方法重新制作。原对标在左，新口播完整结果在右；原对标默认静音，可单独开声。时长按各自内容保留，不强制变速。</p><p>skill已核对：安装版与项目规则一致。这里只展示本轮两组，既有视频不覆盖。</p>'''
for g in groups:
 oid=g['occurrence'];name='整体缩小＋人物背后巨字' if oid=='cg17' else '整体放大＋短语分次落位'
 page+=f'<article id="{oid}"><h2>{oid[2:]} · {name}</h2><p>{html.escape(g["purpose"])}</p><p>来源帧{g["sourceRange"][0]}–{g["sourceRange"][1]}（终点不含） · 新口播{g["rawRange"][0]:.3f}–{g["rawRange"][1]:.3f}s</p><div class="players"><section><h3>原对标</h3><video controls muted playsinline preload="metadata" src="/{g["referenceFile"]}"></video></section><section><h3>新口播完整结果</h3><video controls playsinline preload="metadata" src="/{g["file"]}?v={g["sha256"][:12]}"></video></section></div><button onclick="playPair(this)">两条从头播放</button><button onclick="this.closest(\'article\').querySelectorAll(\'video\').forEach(v=>v.pause())">暂停</button><details><summary>差异与校准证据</summary><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in g['limitations'])+f'</ul><a href="/reviews/final-two/{oid}-encoded-comparison.jpg">编码过程对照</a> · <a href="/reviews/final-two/same-word-calibration.jpg">同字校准</a> · <a href="/{g["input"]}">参数</a> · <a href="/{g["recipe"]}">引用配方</a></details></article>'
page+='''<small>03试作：技术检查不等于用户认可或声音听审；未推进04。</small></main><script>async function playPair(b){document.querySelectorAll('video').forEach(v=>v.pause());const vs=[...b.closest('article').querySelectorAll('video')];vs.forEach(v=>v.currentTime=0);await Promise.all(vs.map(v=>v.play()));}</script></html>''';old.write_text(page,'utf-8');print('two complete candidates ready')
