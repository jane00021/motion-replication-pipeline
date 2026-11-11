import sys,json,copy,hashlib,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[4];sys.path.insert(0,str(P/'source/pilot'))
from components.common import *
from components.runtime import validate_recipe,compose
S=P/'source/pilot/detail-rest/scene';O=P/'render/pilot/detail-rest/scene';R=P/'reviews/detail-rest/scene'
def save(p,v):core.dump(p,v)
def sha(p):return core.file_sha(p)
def style(path,w,h,x,y,outline=0,fill='#fffef7'):
 return {'path':path,'size':44,'inkWidth':w,'inkHeight':h,'anchorX':x,'inkY':y,'align':'center','fill':fill,'outlinePx':outline,'outline':'#111319','shadow':{'dx':.85,'dy':1.3,'blur':.4,'opacity':.85}}
serif='D:/SKILL/font-check/SourceHanSerifSC-Bold.otf';sans='C:/Windows/Fonts/Noto Sans SC Bold (TrueType).otf';A='source/pilot/detail-rest/scene/assets/'
specs=[]
for id in ['cg07','cg08','cg09']:
 c=load(P/f'source/pilot/batches/scene/{id}-input.json');c['detailProfile']='measured-ink-svg-refinement-v1';c['presenterCrop']=[31,76,255,300]
 if id=='cg07':
  c['assets']={'left':A+'cost.png','right':A+'opinions.png'};c['cardBoxes']=[[5,244,133,170],[153,244,128,170]];c['presenterWindow']=[65,37,156]
  c['typeRoles']={'title':style(serif,207,35,143,198),'left':style(serif,69,22,71.5,259,fill='#fff2b8'),'right':style(serif,69,22,217,259,fill='#fff2b8')}
 elif id=='cg08':
  c['assets']={'top':A+'anxiety.png','second':A+'skill.png'};c['topPanelBox']=[17,40,252,136];c['secondPanelBox']=[0,156,286,164];c['presenterBox']=[-3,271,139,247]
  c['typeRoles']={'first':style(sans,201,31,143,88,1.2),'second':style(sans,201,31,143,211,1.2)};c['matteFrames']='source/pilot/detail-rest/scene/matte'
 else:
  c['assets']={'example':A+'experience.png'};c['exampleBox']=[0,156,286,184];c['presenterWindow']=[174,98,97];c['typeRoles']={'caption':style(serif,175,13,143,370)}
 c['frames']=c['frameCount'];specs.append(c);save(S/f'{id}-input.json',c)

def make_recipe(c):
 id=c['occurrence'];r=load(P/f'source/pilot/batches/scene/{id}-recipe.json');r['input']=f'source/pilot/detail-rest/scene/{id}-input.json';r['verificationState']='trial';r['completeGroupValidated']=False
 for ref in r['components'].values():ref['sha256']=sha(P/ref['source'])
 r['supportBindings']={dep:sha(P/dep) for dep in ['source/pilot/components/detail_tools.py','source/pilot/t04_render.py','source/pilot/components/runtime.py','source/pilot/components/pairing.py']}
 for p in (S/'assets').glob('*'):r['supportBindings'][p.relative_to(P).as_posix()]=sha(p)
 
 for dep in ['models/rvm.onnx','models/provenance.json','matte/manifest.json','matte_build.py']:
  if id=='cg08':r['supportBindings']['source/pilot/detail-rest/scene/'+dep]=sha(S/dep)
 r['supportBindings'][f'source/pilot/detail-rest/scene/{id}-input.json']=sha(S/f'{id}-input.json');save(S/f'{id}-recipe.json',r);validate_recipe(r);return r

def encode(c):
 id=c['occurrence'];r=make_recipe(c);src=load(P/'source/pilot/new-input/manifest.json')['path'];N=c['frameCount'];start=c['rawRange'][0];out=O/f'{id}.mp4'
 dec=subprocess.Popen(['ffmpeg','-v','error','-threads','2','-ss',str(start),'-i',src,'-frames:v',str(N),'-vf','fps=30,scale=286:508','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
 enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','286x508','-r','30','-i','pipe:0','-ss',str(start),'-i',src,'-t',str(N/30),'-map','0:v','-map','1:a:0','-vf','scale=572:1016:flags=lanczos','-c:v','libx264','-threads','2','-crf','15','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 for n in range(N):
  b=dec.stdout.read(286*508*3);assert len(b)==286*508*3;raw=Image.frombytes('RGB',(286,508),b);im=compose(r,raw,n,c);enc.stdin.write(im.convert('RGB').tobytes())
  if n in [0,6,N//4,N//2,N*3//4,N-1]:im.save(R/f'{id}-f{n:03d}.png')
 enc.stdin.close();assert enc.wait()==0;assert dec.wait()==0;subprocess.run(['ffmpeg','-v','error','-i',str(out),'-f','null','-'],check=True)
 return {'occurrence':id,'name':c['name'],'file':out.relative_to(P).as_posix(),'referenceFile':f'observations/accepted-review/{id}/reference-clip.mp4','recipe':(S/f'{id}-recipe.json').relative_to(P).as_posix(),'input':(S/f'{id}-input.json').relative_to(P).as_posix(),'frameCount':N,'rawRange':c['rawRange'],'sourceRange':c['sourceRange'],'visualFamily':c['visualFamily'],'subtitleFamily':c['subtitleFamily'],'verificationState':'trial','sha256':sha(out),'limitations':['原字体未确认；候选按角色墨迹盒校准仍有字形差异','SVG为新口播语义示意素材，不代表原片真实案例视频','新口播原声保留；原片音效未重建，词级时间未听审']+(['模型抠像边缘仍需用户复审，不能称任意人物适用'] if id=='cg08' else [])}
if __name__=='__main__':
 groups=[]
 for c in specs:
  print('render',c['occurrence'],flush=True);groups.append(encode(c));save(O/'manifest.json',{'status':'03-refinement-trial','groups':groups})
