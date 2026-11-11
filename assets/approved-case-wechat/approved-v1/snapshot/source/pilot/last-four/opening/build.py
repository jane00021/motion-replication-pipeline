import sys,json,copy,subprocess,hashlib
from pathlib import Path
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'))
from components.common import *
from components.runtime import compose,layers,validate_recipe
S=P/'source/pilot/last-four/opening';O=P/'render/pilot/last-four/opening';R=P/'reviews/last-four/opening';src=load(P/'source/pilot/new-input/manifest.json')['path']
def dump(p,x):core.dump(p,x)
def sha(p):return core.file_sha(p)
def style(path,w,h,x,y,fill='#fffef7',outline=0):return dict(path=path,size=44,inkWidth=w,inkHeight=h,anchorX=x,inkY=y,align='center',fill=fill,outlinePx=outline,outline='#101116',shadow=dict(dx=.85,dy=1.3,blur=.4,opacity=.85))
serif='D:/SKILL/font-check/SourceHanSerifSC-Bold.otf';sans='C:/Windows/Fonts/Noto Sans SC Bold (TrueType).otf'
specs=[]
for num in ['01','02']:
 c=load(P/f'source/pilot/complete01-02/input-{num}.json');c['frameCount']=c['frames'];c['rawRange']=[c['rawStart'],c['rawStart']+c['frames']/30];c['detailProfile']='ink-roles-rvm-original-image-v1'
 if num=='01':
  c['text']['first']='为什么';c['text']['second']='加班到半夜';c['clock']['firstText']=[12,23];c['clock']['secondText']=[31,42];c['typeRoles']={'first':style(serif,66,23,63,323),'second':style(serif,116,22,88,355),'question':style('C:/Windows/Fonts/simsun.ttc',32,47,83,315,'#ab0d30'),'result':style(serif,125,29,191,332)}
 else:
  c['symbol']['assetPath']='source/pilot/detail-rest/circle/assets/warning-red.png';c['symbol']['svgSource']='source/pilot/detail-rest/circle/assets/warning-red.svg';c['symbol'].update(count=14,sizeRange=[26,59],speedRange=[11,18],spinRange=[7,14],nearBlur=1.2,farBlur=.2)
  c['clock'].update(symbolSpawnEnd=42,symbolExitEnd=74,titleStart=52,titleOvershoot=58,titleSettle=65);c['title'].update(inkWidth=278,inkHeight=76,inkX=4,inkY=7);c['typeRoles']={'caption':style(serif,176,12,143,374)};c['matteFrames']='source/pilot/last-four/opening/matte02'
 specs.append(c);dump(S/f'cg{num}-input.json',c)
 r=load(P/f'source/pilot/complete01-02/recipes/{num}.json');r['input']=f'source/pilot/last-four/opening/cg{num}-input.json';r['id']='complete-cg'+num+'-opening-refinement'
 for kind,ref in r['components'].items():ref['source']='source/pilot/components/'+('visual.py' if kind=='visual' else 'subtitle.py');ref['sha256']=sha(P/ref['source'])
 deps=['source/pilot/components/detail_tools.py','source/pilot/t04_render.py','source/pilot/components/runtime.py','source/pilot/components/pairing.py',f'source/pilot/last-four/opening/cg{num}-input.json']
 if num=='01':deps+=[c['asset']]
 else:deps+=[c['symbol']['assetPath'],c['symbol']['svgSource'],'source/pilot/last-four/opening/matte02/manifest.json','source/pilot/last-four/opening/matte.py','source/pilot/detail-rest/scene/models/rvm.onnx']
 r['supportBindings']={p:sha(P/p) for p in deps};dump(S/f'cg{num}-recipe.json',r);validate_recipe(r)

def encode(c):
 id=c['occurrence'];r=load(S/f'{id}-recipe.json');N=c['frames'];start=c['rawStart'];out=O/f'{id}.mp4';alpha=O/id/'rgba';alpha.mkdir(parents=True,exist_ok=True);rows=[]
 dec=subprocess.Popen(['ffmpeg','-v','error','-threads','2','-ss',str(start),'-i',src,'-frames:v',str(N),'-vf','fps=30,scale=286:508','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
 enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','286x508','-r','30','-i','pipe:0','-ss',str(start),'-i',src,'-t',str(N/30),'-map','0:v','-map','1:a:0','-vf','scale=572:1016:flags=lanczos','-c:v','libx264','-threads','2','-crf','15','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 for n in range(N):
  b=dec.stdout.read(286*508*3);assert len(b)==286*508*3;raw=Image.frombytes('RGB',(286,508),b);im=compose(r,raw,n,c);enc.stdin.write(im.convert('RGB').tobytes());ls=layers(r,raw,n,c);a=Image.new('RGBA',(286,508))
  for name in r['layerOrder']:
   if name.startswith('subtitle.') and name in ls:a.alpha_composite(ls[name])
  fp=alpha/f'{n:04d}.png';a.save(fp);rows.append({'frame':n,'sha256':sha(fp),'alphaMax':a.getchannel('A').getextrema()[1]})
  if n in [0,6,N//4,N//2,N*3//4,N-1]:
   im.save(R/f'{id}-f{n:03d}.png')
   for name,v in ls.items():v.save(R/(id+'-'+name.replace('.','-')+f'-f{n:03d}.png'))
 enc.stdin.close();assert enc.wait()==0;assert dec.wait()==0;subprocess.run(['ffmpeg','-v','error','-i',str(out),'-f','null','-'],check=True);dump(O/id/'rgba-manifest.json',{'format':'RGBA PNG no presenter or viewing background in subtitle layer','frames':rows})
 return {'occurrence':id,'name':{'cg01':'暗角工作语境与重点问句接力','cg02':'风险符号下落与人物背后大标题'}[id],'file':out.relative_to(P).as_posix(),'referenceFile':f'observations/accepted-review/{id}/reference-clip.mp4','recipe':(S/f'{id}-recipe.json').relative_to(P).as_posix(),'input':(S/f'{id}-input.json').relative_to(P).as_posix(),'frameCount':N,'rawRange':c['rawRange'],'sourceRange':c['sourceRange'],'visualFamily':c['components']['visual'],'subtitleFamily':c['components']['subtitle'],'sha256':sha(out),'verificationState':'trial','limitations':['原字体身份未确认，候选字形/材质仍需用户复审','新口播原声保留，原片音效尚未重建，词时钟未经听审','新片时长延长，仅可阶段对齐，不冒充原时钟同帧比较']+(['真实工作照片与原工作图片不同'] if id=='cg01' else ['红色警示SVG为风险语义替换，材质与原金币不同','RVM柔边改善人手/头发遮挡，局部发丝仍可有柔边误差'])}
if __name__=='__main__':
 groups=[]
 for c in specs:
  print('render',c['occurrence'],flush=True);groups.append(encode(c));dump(O/'manifest.json',{'status':'03 trial','groups':groups})
