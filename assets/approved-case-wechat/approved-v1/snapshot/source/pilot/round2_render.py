"""Second skill validation: t15 closing phrases + v09 overall enlargement.
Only raw new footage is a render input. Source crops remain read-only comparison evidence.
"""
from pathlib import Path
import json,copy,subprocess,math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
import t04_render as core
import render_migration as media
P=core.P;S=P/'source/pilot/round2';O=P/'render/pilot/round2';S.mkdir(exist_ok=True);O.mkdir(exist_ok=True)
def load(p):return json.loads(Path(p).read_text('utf-8'))
def text_layer(c,n):
 if c.get('profile')=='t15-calibrated-v2':return text_layer_calibrated(c,n)
 out=Image.new('RGBA',(286*4,508*4))
 for role in ['first','second']:
  p=c['phrases'][role];entry=p['entry'];settle=p['settle']
  if n<entry:continue
  tile,m=core.ink(p['text'],c['styles'][role]);t=core.clamp((n-entry)/max(1,settle-entry))
  # First clause travels in from outside left; second separately resolves from a blur.
  if role=='first':
   sx=1;sy=1;x=core.mix(-m['inkWidth']-10,p['x'],1-(1-t)**2)*4-32
  else:
   sx=core.mix(.12,1,1-(1-t)**2);sy=core.mix(1.15,1,t);x=p['x']*4-32+(tile.width*(1-sx))/2
  y=p['y']*4-32
  op=core.clamp((n-entry+1)/3)
  if 'fadeStart' in p:op*=1-core.clamp((n-p['fadeStart'])/(p['clear']-p['fadeStart']))
  core.place(out,tile,x,y,sx,sy,op,1.6*(1-t))
 return out.resize((286,508),Image.Resampling.LANCZOS)
def text_layer_calibrated(c,n):
 """Two real font roles. Ink anchors exclude shadow padding; no frame-end fade."""
 out=Image.new('RGBA',(286*4,508*4))
 for role in ['first','second']:
  p=c['phrases'][role];entry=p['entry'];settle=p['settle']
  if n<entry:continue
  tile,m=core.ink(p['text'],c['styles'][role]);t=core.clamp((n-entry)/max(1,settle-entry))
  dest=p['anchor']-m['inkWidth'] if p.get('align')=='right' else p['anchor']
  sx=sy=1.;blur=0.;op=1.
  if role=='first':
   # Reference first visible f1173, stable f1180; linear travel with deceleration.
   ease=1-(1-t)**2.5;x=core.mix(-m['inkWidth']-4,dest,ease);y=p['y'];blur=.5*(1-t)
  else:
   # Reference f1197..1202: compressed blurred phrase drifts into its right anchor.
   ease=1-(1-t)**2;sx=core.mix(.68,1,ease);sy=core.mix(1.13,1,ease)
   inkRight=p['anchor']+p.get('travelX',25)*(1-ease)
   x=inkRight-m['inkWidth']*sx;y=p['y']-p.get('travelY',10)*(1-ease)
   blur=p.get('entryBlur',2.4)*(1-t)**1.5;op=core.clamp((n-entry+1)/4)
  core.place(out,tile,x*4-32*sx,y*4-32*sy,sx,sy,op,blur)
 return out.resize((286,508),Image.Resampling.LANCZOS)

def main():
 assert load(P/'.pipeline/state.json')['stages'][3]['status']=='active'
 base=load(P/'source/pilot/t04/input-A.json')['roles']['body'];base['size']=22
 cfg={'reference':{'occurrence':'cg19','family':'t15','frames':[1172,1218],'sourceClock':'zero-based, end-exclusive'},'frames':78,'rawStart':41.2,'phrases':{'first':{'text':'一步一步来','x':14,'y':335,'entry':3,'settle':12},'second':{'text':'生活慢慢变好','x':143,'y':378,'entry':37,'settle':48}},'styles':{'first':copy.deepcopy(base),'second':copy.deepcopy(base)},'sameWord':{'frames':46,'phrases':{'first':{'text':'才是普通人','x':14,'y':335,'entry':3,'settle':12},'second':{'text':'该走的路','x':143,'y':378,'entry':21,'settle':29}}},'expression':'前句建立做法，后句承接结果；不是金色重点词模板，不额外着色。','endBehavior':'原参考到文件结束仍有文字，不凭空添加退场；透明序列最后一帧非空是如实保留。','unknowns':['原字体身份未完全确认','压缩和动手遮挡造成准确字面测量误差约2px','新句时点来自原片机器语音候选，未完成听审']}
 core.dump(S/'subtitle-input.json',cfg)
 vis={'reference':{'occurrence':'cg18','family':'v09','frames':[1135,1169]},'frames':34,'rawStart':22.5,'keyframes':[{'frame':0,'rect':[10,23,272,490]},{'frame':1,'rect':[10,24,268,490]},{'frame':2,'rect':[5,14,274,498]},{'frame':3,'rect':[0,6,278,502]},{'frame':4,'rect':[0,0,283,508]},{'frame':5,'rect':[0,0,284,508]},{'frame':12,'rect':[0,0,286,508]}],'method':'native source bright room top border & visible inset edges; x2/y2 bottom edge approximate2px','expression':'整体从缩小状态回到满画幅，接回人物表达；使用新片自身透视与人物，不借旧像素。','excludedComponent':'t14半透明短语板是同一原片中的独立字幕组件，本次只测试v09画面缩放，明确不声称完整组合已复刻。'}
 core.dump(S/'visual-input.json',vis)
 raw=media.extract(cfg['rawStart'],cfg['frames']/30);aud=media.audio('round2-subtitle',cfg['rawStart'],cfg['frames']/30);frames=[];alphadir=O/'subtitle-rgba';alphadir.mkdir(exist_ok=True);seq=[]
 for n,a in enumerate(raw):
  alpha=text_layer(cfg,n);alpha.save(alphadir/f'{n:04d}.png');seq.append({'frame':n,'alphaBBox':alpha.getchannel('A').getbbox()})
  im=Image.fromarray(a).convert('RGBA');im.alpha_composite(alpha.resize((628,1118),Image.Resampling.LANCZOS));frames.append(im.convert('RGB'))
  if n in [3,12,37,48,70]:im.save(O/f'subtitle-frame-{n}.png')
 media.encode(O/'subtitle-applied.mp4',frames,aud);core.dump(alphadir/'sequence.json',{'fps':30,'canvas':[286,508],'frames':seq,'endNotClear':'reference ends while caption still visible'})
 # Same word static/time calibration output on separate neutral preview only for engineering QA.
 same=copy.deepcopy(cfg);same['phrases']=cfg['sameWord']['phrases'];sf=[]
 for n in range(46):
  im=Image.new('RGBA',(286,508),'#263036');im.alpha_composite(text_layer(same,n));sf.append(im.convert('RGB').resize((628,1118),Image.Resampling.LANCZOS))
 media.encode(O/'subtitle-same.mp4',sf,media.audio('round2-same',41.2,46/30))
 raw=media.extract(vis['rawStart'],34/30);frames=[];rects=[]
 for n,a in enumerate(raw):
  keys=vis['keyframes'];lo=max((k for k in keys if k['frame']<=n),key=lambda k:k['frame']);hi=next((k for k in keys if k['frame']>n),lo);t=0 if hi==lo else (n-lo['frame'])/(hi['frame']-lo['frame']);rect=[core.mix(x,y,t) for x,y in zip(lo['rect'],hi['rect'])]
  x0,y0,x1,y1=rect;box=[round(x0*628/286),round(y0*1118/508),round(x1*628/286),round(y1*1118/508)];im=Image.new('RGB',(628,1118));im.paste(Image.fromarray(a).resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS),(box[0],box[1]));frames.append(im);rects.append({'frame':n,'nativeRect':rect})
  if n in [0,2,4,12,25]:im.save(O/f'visual-frame-{n}.png')
 media.encode(O/'visual-applied.mp4',frames,media.audio('round2-visual',vis['rawStart'],34/30));core.dump(O/'visual-rects.json',rects)
 core.dump(O/'manifest.json',{'status':'two-new-trials-not-user-approved','subtitle':'t15/cg19','visual':'v09/cg18 visual component only','rawInput':load(P/'source/pilot/new-input/manifest.json'),'source':'source/pilot/round2_render.py','clips':{name:core.file_sha(O/name) for name in ['subtitle-applied.mp4','visual-applied.mp4','subtitle-same.mp4']},'previousApprovedT04':'reviews/t04-user-approval.json','stageAccepted':False})
 # Stable new page: each new group has exactly two media players.
 old=(P/'render/pilot/index.html').read_text('utf-8');(P/'reviews/t04-calibration/approved-two-player.html').write_text(old,'utf-8')
 head=old[:old.index('<main>')]
 body='<main><h1>第二轮复刻检验</h1><p>每组只保留原对标与新口播应用结果。两组均为首次试作，等待你检验。</p>'
 for typ,title,ref,desc in [('subtitle','字幕：收尾双句接力','cg19','参考39.067–40.600秒；新口播41.200–43.800秒。前句“一步一步来”，后句“生活慢慢变好”。'),('visual','画面：整体回放大','cg18','参考37.833–38.967秒；新口播22.500–23.633秒。本组测试整体画面回放大；原参考中的短语板属于另一个字幕组件，本次未叠加。')]:
  body+=f'<article style="margin:28px 0"><h2>{title}</h2><p>{desc}</p><div class="columns"><section><h2>原对标</h2><video controls muted playsinline preload="auto" src="../../observations/accepted-review/{ref}/reference-clip.mp4"></video></section><section><h2>新口播应用</h2><video controls playsinline preload="auto" src="round2/{typ}-applied.mp4?revision=round2-r1"></video></section></div><button onclick="playPair(this)">两条从头播放</button><button onclick="this.closest(\'article\').querySelectorAll(\'video\').forEach(v=>v.pause())">暂停</button></article>'
  body+=''
 body+='<small>03-pilot 新代表组待检验；原对标中的成片字幕与画面层分开计，不把组件测试当完整组合通过。</small></main><script>async function playPair(b){for(const v of b.closest("article").querySelectorAll("video")){v.currentTime=0;await v.play();}}</script></html>'
 (P/'render/pilot/index.html').write_text(head+body,'utf-8')
 print(json.dumps({'newSubtitle':'t15','newVisual':'v09','newPlayers':4}))
if __name__=='__main__':main()
