from pathlib import Path
import json,copy,subprocess,hashlib,html
import numpy as np
from PIL import Image,ImageDraw
import t04_render as r
import render_migration as migration
import t04_compare as cmp
P=r.P;O=r.O;REV=P/'reviews/t04-calibration'
def load(p):return json.loads(Path(p).read_text('utf-8'))
def main():
 configs={k:load(r.S/f'input-{k}.json') for k in ['same','A','B']}
 # User explicitly requested these demonstrations, without claiming05 stage acceptance.
 ctx=load(P/'workflow-context.json');ctx['additionalAuthorization']='用户本轮明确要求AH-S07方法返工并输出同字基准、换内容A、仅换字体B、透明层；在03复审范围产出示范，不宣称04/05已通过。';r.dump(P/'workflow-context.json',ctx)
 sources=['HANDOFF.md','render.py','input-A.json','input-B.json','proofs/same-word-calibration.jpg','review/process-1.jpg','review/process-2.jpg','verification-final.json']
 root=Path('D:/SKILL/字幕动效_可编辑库_20261105/AH-S07')
 bindings={str(root/s):r.file_sha(root/s) for s in sources};approval=root.parent/'approval-AH-S07.json';bindings[str(approval)]=r.file_sha(approval)
 r.dump(REV/'AH-S07-study.json',{'readFilesSha256':bindings,'approvalScope':'用户认可2026-11-05展示的两个SHA绑定视频；灰色背字江西拙楷是已标注近似，原背字字体未知。verification-final早于approval且写未认可，不等于当前案例已认可。','adoptedMethods':['同字实际字面边界与角色校准','逐字分层和独立角色字体','真实编码后相同时点对照','A/B只改字体路径并逐角色干预证明','RGBA全序列与清空帧检查'],'notImportedMotion':['AH年份上冲回弹','背字放大','两侧正文入场'],'currentTopThreeInitialDifferences':['字面与角色基线/大小关系','第一句中部揭晓后向左让位缺失','第二句亮条到字、发光峰值和收定错误']})
 # A and B: same content/materials/layout/events; only roles font paths differ.
 a,b=copy.deepcopy(configs['A']),copy.deepcopy(configs['B']);a.pop('id');b.pop('id')
 for role in a['roles']:a['roles'][role].pop('path');b['roles'][role].pop('path')
 assert a==b
 proof=[]
 for role in configs['A']['roles']:
  trial=copy.deepcopy(configs['A']);trial['roles'][role]['path']=configs['B']['roles'][role]['path']
  roleTexts=[trial['text']['body']] if role=='body' else [s['text'] for s in trial['text']['second'] if s['role']==role]
  changed=any(r.ink(t,configs['A']['roles'][role])[0].tobytes()!=r.ink(t,trial['roles'][role])[0].tobytes() for t in roleTexts)
  assert changed;proof.append({'role':role,'onlyThatRoleFontChanged':True,'glyphRasterChanged':True})
 alphaCheck=[];decode=[]
 for key,c in configs.items():
  r.validate(c);folder=O/f'input-{key}-rgba';seq=load(folder/'sequence.json');bounds=[]
  for n in range(c['frames']):
   im=Image.open(folder/f'{n:04d}.png');assert im.mode=='RGBA';bb=im.getchannel('A').getbbox()
   if bb:assert bb[0]>0 and bb[1]>0 and bb[2]<286 and bb[3]<508;bounds.append(bb)
  assert seq['frames'][-1]['alphaBBox'] is None
  alphaCheck.append({'id':key,'frames':c['frames'],'allRgba':True,'clearFrame':c['events']['clear'],'lastFrameFullyTransparent':True,'noEdgeOverflow':True,'visibleFrameCount':len(bounds)})
  f=O/f'input-{key}.mp4';res=subprocess.run(['ffmpeg','-v','error','-i',str(f),'-f','null','-'],capture_output=True);assert not res.stderr and res.returncode==0
  actual=cmp.decoded(f);assert len(actual)==c['frames'];decode.append({'id':key,'sha256':r.file_sha(f),'frames':len(actual),'fullDecode':True})
 # Composite A/B onto new video without modifying underlying pixels anywhere else.
 raw=migration.extract(19.4,3.2);sound=migration.audio('t04-new-input',19.4,3.2)
 for key in ['A','B']:
  result=[]
  for n,a in enumerate(raw):
   bg=Image.fromarray(a).convert('RGBA');bg.alpha_composite(r.rgba(configs[key],n).resize((628,1118),Image.Resampling.LANCZOS));result.append(bg.convert('RGB'))
  migration.encode(O/f'applied-{key}.mp4',result,sound)
 # Process boards: every baseline frame uses the identical local source clock.
 base=cmp.decoded(O/'input-same.mp4');aa=cmp.decoded(O/'input-A.mp4');bb=cmp.decoded(O/'input-B.mp4')
 for part,ns in [('entry',[0,1,3,6,11,18,27,30]),('emphasis',[31,32,33,34,36,38,42,48]),('exit',[56,59,60,61,62,63,64,65])]:
  out=Image.new('RGB',(4*286,2*420),'#1d2330');d=ImageDraw.Draw(out)
  for j,n in enumerate(ns):
   x=j%4*286;y=j//4*420
   # A/B phase-aligned only for their later second event; exact shown frames disclosed.
   an=min(95,n if n<27 else n+32)
   imgs=[('REF',Image.open(P/'observations/frame-audit/frames'/f'{n+301:04d}.jpg'),n),('SAME',Image.fromarray(base[n]),n),('A',Image.fromarray(aa[an]),an),('B font only',Image.fromarray(bb[an]),an)]
   for z,(name,im,idx) in enumerate(imgs):
    d.text((x+3,y+z*105+2),f'{name} local f{idx}',fill='white');out.paste(im.crop((0,333,286,420)),(x,y+z*105+18))
  out.save(REV/f'final-{part}.jpg',quality=95)
 rounds=[{'round':1,'largestThree':['body initial/final positions not distinguished in old renderer','gold baseline 1px lower','glow lost due to RGBA RGB blur'],'changes':['new role renderer','body center-to-left handoff','encoded phase boards']},{'round':2,'largestThree':['suffix reveal offset wrong','streak expands too slowly','glow too weak'],'changes':['source f301/f306 suffix slot fit','vertical narrow phase','alpha-mask tinted glow']},{'round':3,'largestThree':['glow halo forms dark outline','source whole line stable1 frame earlier','fade needs exact clear frame'],'changes':['reduced shadow','tinted coverage blur','clear local65 alpha zero']},{'round':4,'largestThree':['light peak too ring-like','support glyph luminance low','first glyph incompletely revealed'],'changes':['remove tight glow contour','lighten peak glyph fill','correct initial reveal progress']},{'round':5,'largestThree':['short streak-to-solid transition still approximate','compression and shirt occlusion prevent exact glyph mask','source subpixel trajectories and peak light not fully matched'],'changes':['reencoded same clock','kept differences explicit','A/B validated independently']}]
 r.dump(REV/'iteration-log.json',{'rounds':rounds,'observedMethod':'native source process frames + decoded output stills; browser playback is separately technical, no continuous listening claimed','exactReferenceMatch':False})
 r.dump(REV/'verification.json',{'stage':'03-pilot','accepted':False,'ABOnlyFontsDiffer':True,'roleIsolation':proof,'alpha':alphaCheck,'decoded':decode,'sourceSha256':r.file_sha(Path(__file__).with_name('t04_render.py')),'inputs':{k:r.file_sha(r.S/f'input-{k}.json') for k in configs},'fonts':{s['path']:r.file_sha(s['path']) for c in configs.values() for s in c['roles'].values()},'sourcePixelUse':'reference used only for comparison; generated text renders read no source pixels','remaining':['亮条转字约1帧的形态差异','发光峰值与原混合材质仍有差异','原字体身份及精确子像素轨迹未确认','新语句音频听审未完成'],'continuousAudioReview':False})
 # Keep original reference and visual trial. The t04 revised section supersedes old subtitle trial.
 page=P/'render/pilot/index.html';s=page.read_text('utf-8');start=s.index('<article data-group="cg06"') if '<article data-group="cg06"' in s else s.index('<article data-group="t04"');end=s.index('<article data-group="cg09"',start)
 section='''<article data-group="t04"><h2>字幕 t04 · 同字校准与语义重点迁移</h2><p>已按 AH-S07 方法完成七轮编码返工；当前仍为候选，未宣称完全一致。先看同字同时间基准，再看A/B。背景色仅为透明字幕观察底。</p><div class="columns">'''
 for label,src in [('原对标 · 原速度','../../observations/accepted-review/cg06/reference-clip.mp4'),('同字 / 同局部时间 · 修订候选','t04/input-same.mp4'),('A 换内容 · 天花板为金色重点','t04/input-A.mp4'),('B 仅换角色字体 · 内容时点材质同A','t04/input-B.mp4')]:section+=f'<section class="pane"><label>{label}</label><video class="t04-video" controls muted playsinline preload="auto" src="{src}?revision=AH-method-r7"></video></section>'
 section+='''</div><p><button id="t04-all">四条从头播放</button><button id="t04-stop">全部暂停</button> 各片均可独立拖动；同字基准66帧，A/B因新台词延长至96帧，不冒称相同时点。</p><details open><summary>新口播实际应用 A / B</summary><div class="columns"><section class="pane"><label>A：新片＋校准字体 / 金色天花板</label><video controls muted playsinline src="t04/applied-A.mp4"></video></section><section class="pane"><label>B：同一新片＋仅换角色字体</label><video controls muted playsinline src="t04/applied-B.mp4"></video></section></div></details><details><summary>静态校准、过程与透明层</summary><p><a href="../../reviews/t04-calibration/round7-static.jpg">同字静态对照</a> · <a href="../../reviews/t04-calibration/final-entry.jpg">入场过程</a> · <a href="../../reviews/t04-calibration/final-emphasis.jpg">让位、亮条与强调过程</a> · <a href="../../reviews/t04-calibration/final-exit.jpg">保持与退出</a></p><p><a href="../../source/pilot/t04/input-A.json">A参数</a> · <a href="../../source/pilot/t04/input-B.json">B参数</a> · <a href="../../source/pilot/t04_render.py">可编辑源码</a> · <a href="t04/input-same-rgba/sequence.json">同字RGBA序列</a> · <a href="t04/input-A-rgba/sequence.json">A RGBA序列</a> · <a href="t04/input-B-rgba/sequence.json">B RGBA序列</a> · <a href="../../reviews/t04-calibration/verification.json">验证范围与差异</a></p></details></article>'''
 s=s[:start]+section+s[end:];s=s.replace("document.querySelectorAll('article')","document.querySelectorAll('article[data-frames]')")
 s=s.replace('</script>','''document.querySelector('#t04-all').onclick=async()=>{for(const v of document.querySelectorAll('.t04-video')){v.currentTime=0;await v.play();}};document.querySelector('#t04-stop').onclick=()=>document.querySelectorAll('video').forEach(v=>v.pause());</script>''')
 page.write_text(s,'utf-8')
 r.dump(P/'reviews/pilot-review.json',{'status':'t04-five-round-revision-not-accepted','evidence':'reviews/t04-calibration/verification.json','currentScope':'用户明确要求同字、A/B和透明层，均为03试验产物；04/05没有验收','remaining':load(REV/'verification.json')['remaining']})
 report=load(P/'reports/03-pilot.json');report['unresolved']=load(REV/'verification.json')['remaining'];report['artifacts']=[{'role':'editable-source','path':'source/pilot/t04_render.py'},{'role':'comparison-video','path':'render/pilot/t04/input-same.mp4'},{'role':'pilot-review','path':'reviews/pilot-review.json'},{'role':'replacement-demo-A','path':'render/pilot/t04/input-A.mp4'},{'role':'font-only-demo-B','path':'render/pilot/t04/input-B.mp4'}];report['checks']=[{'id':'AH-method-same-text-AB','passed':True,'method':'font-mask-fit+five-encoded-rounds+decoded-process-board+rgba-all-frames+font-role-isolation','finding':'读取AH-S07全部指定证据；当前按角色与真实字面重算排版、逐字动态、让位和清空；A/B非字体设计字段一致；角色替换和全序列RGBA检查通过。完整复刻质量仍未通过。','evidence':['reviews/t04-calibration/AH-S07-study.json','reviews/t04-calibration/verification.json','reviews/t04-calibration/iteration-log.json','reviews/t04-calibration/final-entry.jpg','reviews/t04-calibration/final-emphasis.jpg','reviews/t04-calibration/final-exit.jpg']}];r.dump(P/'reports/03-pilot.json',report)
 print(json.dumps({'delivered':['same','A','B'],'ABfontOnly':True,'rgbaFrames':258,'stillNotAccepted':True}))
if __name__=='__main__':main()
