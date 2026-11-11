from pathlib import Path
import sys,json,subprocess,copy,html
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'))
from components.detail_tools import *
from components.runtime import compose,layers,validate_recipe
R=P/'reviews/detail-two';S=P/'source/pilot/detail-two';O=P/'render/pilot/detail-two'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',13)
# Real same-word role calibration with original cropped glyph region, no reference glyph in rendering.
rows=[('cg04','context','经济环境','0238.jpg',[20,61,140,99]),('cg04','statement','彻底改变','0238.jpg',[16,101,161,157]),('cg13','second','永远优先','0853.jpg',[52,310,232,365])]
sheet=Image.new('RGB',(800,3*170),'#25313d');d=ImageDraw.Draw(sheet)
for i,(oid,role,text,fr,bb) in enumerate(rows):
 c=load(S/f'{oid}-input.json');sp=c['typeRoles'][role];ref=Image.open(P/'observations/frame-audit/frames'/fr).crop(bb)
 sheet.paste(ref.resize((ref.width*2,ref.height*2)),(8,i*170+30));d.text((8,i*170+5),'原片同字 '+text,font=font,fill='white')
 bg=Image.new('RGBA',(370,135),'#587386');sp=copy.deepcopy(sp);sp['inkWidth']=sp['inkWidth']*2;sp['inkHeight']*=2;sp['outlinePx']*=2
 im,sz=glyph_tile(text,json.dumps(sp,sort_keys=True));bg.alpha_composite(im,(5,10));sheet.paste(bg.convert('RGB'),(410,i*170+25));d.text((410,i*170+5),'候选字形＋测量比例＋材质（非原字体确认）',font=font,fill='white')
sheet.save(R/'same-word-selected-calibration.jpg')
qa=[];groups=[]
for oid in ['cg04','cg13']:
 c=load(S/f'{oid}-input.json');recipe=load(S/f'{oid}-recipe.json');validate_recipe(recipe);N=c['frames'];start,end=c['sourceRange'] if oid=='cg04' else c['referenceFrames']
 frames=subprocess.check_output(['ffmpeg','-v','error','-i',str(O/f'{oid}.mp4'),'-vf','scale=286:508','-f','rawvideo','-pix_fmt','rgb24','pipe:1']);decoded=np.frombuffer(frames,np.uint8).reshape(-1,508,286,3);assert len(decoded)==N
 sheet=Image.new('RGB',(7*300,1065),'#1a2530');d=ImageDraw.Draw(sheet)
 for j,n in enumerate(np.linspace(0,N-1,7,dtype=int)):
  sf=start+round(n/(N-1)*(end-start-1));ref=Image.open(P/'observations/frame-audit/frames'/f'{sf+1:04d}.jpg');sheet.paste(ref,(j*300,30));sheet.paste(Image.fromarray(decoded[n]),(j*300,552));d.text((j*300+4,5),f'原片f{sf}／新片f{n} 阶段对照',font=font,fill='white')
 sheet.save(R/f'{oid}-encoded-phase-comparison.jpg')
 # Independent recomposition and deterministic rendering check.
 n=N//2;rawpath=R/f'{oid}-raw.png';src=load(P/'source/pilot/new-input/manifest.json')['path']
 subprocess.run(['ffmpeg','-v','error','-y','-ss',str(c['rawRange'][0]+n/30),'-i',src,'-frames:v','1','-vf','scale=286:508',str(rawpath)],check=True)
 raw=Image.open(rawpath).convert('RGBA');tiles=layers(recipe,raw,n,c);comp=Image.new('RGBA',(286,508))
 for key in recipe['layerOrder']:
  if key in tiles:comp.alpha_composite(tiles[key])
 assert np.array_equal(np.asarray(comp),np.asarray(compose(recipe,raw,n,c)))
 for key,im in tiles.items():
  if key.startswith('subtitle.'):im.save(R/f'{oid}-{key}.png')
 changed=copy.deepcopy(c)
 if oid=='cg04':changed['text']['change']='检验改字'
 else:changed['subtitle']['text']['second']='检验改字'
 changedpx=int(np.any(np.asarray(comp)!=np.asarray(compose(recipe,raw,n,changed)),2).sum());assert changedpx>0
 if oid=='cg04':
  assert recipe['layerOrder'].index('visual.presenter')>recipe['layerOrder'].index('visual.example')
  differences=['原片城市与真人工作素材改为新内容SVG示意，视觉材质不同；不是原作者SVG源码','粗黑标题字形仍为Noto候选人工加重，笔画端点与原片窄黑体有差异','动作与新口播时长按阶段调整；新音轨保留，原音效未独立重建且未听审']
 else:differences=['原片钞票改为技能主题SVG，透明叠放关系保留，素材质感仍不同','宋体角色采用候选字体，原字体身份未确认；数字2的斜切轮廓仍为近似','字词时间及声音未人工听审；圆窗是几何裁切，未验证通用人物抠像']
 qa.append({'occurrence':oid,'sha256':core.file_sha(O/f'{oid}.mp4'),'frameCount':N,'fullDecode':True,'independentLayerRecomposition':True,'textEditChangesPixels':changedpx,'remainingLargestThree':differences,'userApproved':False,'noGeneralMattingClaim':True})
 groups.append({'occurrence':oid,'name': '斜切场景与分角色标题' if oid=='cg04' else '透明技能素材与重点句接管','file':f'render/pilot/detail-two/{oid}.mp4','referenceFile':f'observations/accepted-review/{oid}/reference-clip.mp4','rawRange':c['rawRange'],'sourceRange':[start,end],'recipe':f'source/pilot/detail-two/{oid}-recipe.json','input':f'source/pilot/detail-two/{oid}-input.json','sha256':core.file_sha(O/f'{oid}.mp4'),'status':'03-trial-awaiting-user-review','differences':differences})
core.dump(R/'verification.json',{'groups':qa,'fontFiles':{key:{'path':path,'sha256':core.file_sha(path)} for key,path in load(S/'fonts.json').items()},'svgSources':{p.name:core.file_sha(p) for p in (S/'assets').glob('*.svg')},'scope':'two groups only; no 04 acceptance; other media frozen','previousFailure':'prior all17 integration exact recomposition did not pass; current two tested separately'})
core.dump(O/'metadata.json',{'groups':groups,'stage':'03-pilot','accepted':False})
old=P/'render/pilot/index.html';(R/'frozen17-panel.html').write_text(old.read_text('utf-8'),'utf-8')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>两组细节校准 · 待核验</title><style>body{background:#111b28;color:#eaf1fa;font:16px/1.7 "Microsoft YaHei";margin:0}main{max-width:1160px;margin:auto;padding:26px}article{padding:22px;background:#1a2737;border:1px solid #3a526d;border-radius:14px;margin:25px 0}.players{display:grid;grid-template-columns:1fr 1fr;gap:24px}video{width:100%;height:620px;background:#030609;object-fit:contain}button{padding:10px 18px;margin:10px 12px 10px 0;color:white;background:#26496f;border:1px solid #76a0ce;border-radius:6px;font:inherit}a{color:#96c7ff}h2{font-size:23px}small{color:#bed0e5}details{margin-top:15px}@media(max-width:700px){main{padding:10px}article{padding:12px}video{height:420px}.players{gap:10px}}</style><main><h1>两组细节校准 · 待你核验</h1><p>本轮只返工04、13。原对标在左，新口播结果在右。原对标默认静音，可单独开声；两条保留各自速度。</p><p>重点检查：字形与材质、实际字面居中、斜切前后层序、圆窗脸部边界、透明SVG叠放和表达接管。原字体身份与通用抠像尚未确认。</p>'''
for g in groups:
 oid=g['occurrence'];page+=f'<article id="{oid}"><h2>{oid[2:]} · {g["name"]}</h2><p>对标帧 {g["sourceRange"][0]}–{g["sourceRange"][1]}（终点不含） · 新口播 {g["rawRange"][0]:.3f}–{g["rawRange"][1]:.3f}s</p><div class="players"><section><h3>原对标</h3><video controls playsinline muted preload="metadata" src="/{g["referenceFile"]}"></video></section><section><h3>新口播完整结果</h3><video controls playsinline preload="metadata" src="/{g["file"]}?v={g["sha256"][:12]}"></video></section></div><button onclick="playPair(this)">两条从头播放</button><button onclick="this.closest(\'article\').querySelectorAll(\'video\').forEach(v=>v.pause())">暂停</button><details><summary>当前差异与校准证据</summary><ul>'+''.join('<li>'+html.escape(s)+'</li>' for s in g['differences'])+f'</ul><a href="/reviews/detail-two/{oid}-encoded-phase-comparison.jpg">编码后的阶段对照</a> · <a href="/reviews/detail-two/same-word-selected-calibration.jpg">同字静态校准</a> · <a href="/{g["input"]}">编辑参数</a> · <a href="/{g["recipe"]}">引用配方</a></details></article>'
page+='''<p>SVG源文件：<a href="/source/pilot/detail-two/assets/business-skyline.svg">城市</a> · <a href="/source/pilot/detail-two/assets/business-risk-desk.svg">风险工作台</a> · <a href="/source/pilot/detail-two/assets/practical-skills-spread.svg">技能素材组</a></p><small>03-pilot待核验；只展示两组，未推进04，未将方法写成已验证技能规则。</small></main><script>async function playPair(b){document.querySelectorAll('video').forEach(v=>v.pause());const vs=[...b.closest('article').querySelectorAll('video')];vs.forEach(v=>v.currentTime=0);await Promise.all(vs.map(v=>v.play()));}</script></html>'''
old.write_text(page,'utf-8');print('2-group page ready')
