from pathlib import Path
import sys,json,copy,hashlib,subprocess,shutil
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from components import closing_batch as comp
from components.common import *
from PIL import Image,ImageDraw
ROOT=P;S=P/'source/pilot/batches/closing';O=P/'render/pilot/batches/closing';R=P/'reviews/batches/closing'
def rel(p):return str(Path(p).relative_to(P)).replace('\\','/')
def dump(p,x):core.dump(p,x)
def sha(p):return core.file_sha(p)
style=copy.deepcopy(load(P/'source/pilot/t04/input-A.json')['roles']['body']);style.update(size=22,fill='#f7f7f0')
vis18=load(P/'source/pilot/round2/visual-input.json')
sub19=load(P/'source/pilot/round2/subtitle-input.json');sub19['phrases']['second']['x']=139;sub19['styles']['second']['size']=21
cases=[
 {'occurrence':'cg06','name':'解释句让位与金色重点词揭晓','sourceRange':[300/30,366/30],'sourceFrames':[300,366],'rawRange':[19.4,22.6],'frameCount':96,'visualFamily':None,'subtitleFamily':'t04','subtitle':{'parameterPath':'source/pilot/t04/input-A.json'},'approvedFile':'render/pilot/t04/applied-A.mp4'},
 {'occurrence':'cg17','name':'整体缩入与人物背后巨字接管','sourceRange':[1103/30,1136/30],'sourceFrames':[1103,1136],'rawRange':[26.82,29.32],'frameCount':75,'visualFamily':'v08','subtitleFamily':'t13','visual':{'keyframes':[{'frame':0,'rect':[0,0,286,508]},{'frame':12,'rect':[9,20,270,486]},{'frame':74,'rect':[9,20,270,486]}]},'subtitle':{'rows':[{'text':'本事','inkWidth':137,'inkHeight':67,'x':-4,'y':-6,'entry':3,'settle':13,'drift':-39,'repeatEvery':153},{'text':'落地','inkWidth':144,'inkHeight':64,'x':-4,'y':148,'entry':4,'settle':14,'drift':35,'repeatEvery':153}],'caption':'学个能落地的本事','exit':[65,74]}},
 {'occurrence':'cg18','name':'整体回到满屏与左右短语板接力','sourceRange':[1135/30,1169/30],'sourceFrames':[1135,1169],'rawRange':[38.82,40.52],'frameCount':51,'visualFamily':'v09','subtitleFamily':'t14','visual':{'keyframes':vis18['keyframes']},'subtitle':{'style':style,'phrases':[{'text':'要踏实','rect':[12,282,100,43],'plateIn':[5,9],'textStart':8,'stagger':2},{'text':'别求快','rect':[170,263,104,43],'plateIn':[18,22],'textStart':22,'stagger':2}],'exit':[45,50]}},
 {'occurrence':'cg19','name':'收尾双句错位接力','sourceRange':[1172/30,1218/30],'sourceFrames':[1172,1218],'rawRange':[41.2,43.8],'frameCount':78,'visualFamily':None,'subtitleFamily':'t15','subtitle':sub19}]
orders={'cg06':['visual.presenter','subtitle.text'],'cg17':['visual.stage','visual.inset','subtitle.behindTitle','visual.presenterForeground','subtitle.speechCaption'],'cg18':['visual.presenter','subtitle.phrasePlates'],'cg19':['visual.presenter','subtitle.text']}
rawpath=load(P/'source/pilot/new-input/manifest.json')['path']
manifest=[]
for c in cases:
 id=c['occurrence'];folder=O/id;folder.mkdir(parents=True,exist_ok=True);alpha=folder/'subtitle-rgba';alpha.mkdir(exist_ok=True)
 inp=S/(id+'-input.json');dump(inp,c)
 refs={}
 if c['visualFamily']:refs['visual']={'id':c['visualFamily'],'entrypoint':'components.closing_batch:render','source':'source/pilot/components/closing_batch.py','sha256':sha(Path(comp.__file__))}
 else:refs['visual']={'id':None,'entrypoint':'components.runtime:passthrough','source':'source/pilot/components/runtime.py','sha256':sha(P/'source/pilot/components/runtime.py')}
 refs['subtitle']={'id':c['subtitleFamily'],'entrypoint':'components.closing_batch:render_subtitle','source':'source/pilot/components/closing_batch.py','sha256':sha(Path(comp.__file__))}
 deps=['source/pilot/t04_render.py','source/pilot/components/visual.py','source/pilot/round2_render.py']
 if id=='cg06':deps.append(c['subtitle']['parameterPath'])
 recipe={'occurrence':id,'completeGroupValidated':False,'verificationState':'trial','id':id,'status':'03-trial','components':refs,'layerOrder':orders[id],'input':rel(inp),'sharedStyle':'source/pilot/complete01-02/shared-text-style.json','commonSha256':sha(P/'source/pilot/components/common.py'),'sharedStyleSha256':sha(P/'source/pilot/complete01-02/shared-text-style.json'),'supportBindings':{p:sha(P/p) for p in deps}}
 rp=S/(id+'-recipe.json');dump(rp,recipe)
 if id=='cg06':
  fp=P/c['approvedFile'];assert sha(fp)==load(P/'reviews/t04-user-approval.json')['sha256'];state='user-approved-specific-media';technical={'existingApprovedMediaPreserved':True,'sha256':sha(fp)}
 else:
  count=c['frameCount'];duration=count/30;aud=folder/'audio.wav';subprocess.run(['ffmpeg','-v','error','-y','-ss',str(c['rawRange'][0]),'-i',rawpath,'-t',str(duration),'-vn','-ac','1',str(aud)],check=True)
  dec=subprocess.Popen(['ffmpeg','-v','error','-ss',str(c['rawRange'][0]),'-i',rawpath,'-t',str(duration),'-vf','fps=30,scale=286:508','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
  fp=folder/'complete-applied.mp4';enc=subprocess.Popen(['ffmpeg','-v','error','-threads','2','-y','-f','rawvideo','-pix_fmt','rgb24','-s','286x508','-r','30','-i','pipe:0','-i',str(aud),'-c:v','libx264','-threads','2','-crf','15','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-shortest','-movflags','+faststart',str(fp)],stdin=subprocess.PIPE)
  samples=set([0,3,8,12,round(count*.5),count-7,count-1]);rows=[];frames=[]
  for n in range(count):
   data=dec.stdout.read(286*508*3)
   if len(data)!=286*508*3:raise RuntimeError('Raw frame truncated '+id+str(n))
   raw=Image.frombytes('RGB',(286,508),data).convert('RGBA');vis=comp.render(c['visualFamily'],raw,n,c) if c['visualFamily'] else {'presenter':raw};subs=comp.render_subtitle(c['subtitleFamily'],n,c);layers={**{'visual.'+k:v for k,v in vis.items()},**{'subtitle.'+k:v for k,v in subs.items()}}
   out=Image.new('RGBA',(286,508));sub=out.copy()
   for k in orders[id]:
    if k in layers:out.alpha_composite(layers[k])
   for v in subs.values():sub.alpha_composite(v)
   sub.save(alpha/f'{n:04d}.png');rows.append({'frame':n,'alphaBBox':sub.getchannel('A').getbbox()});enc.stdin.write(out.convert('RGB').tobytes())
   if n in samples:out.save(folder/f'frame-{n:03d}.png')
  enc.stdin.close();assert enc.wait()==0;assert dec.wait()==0
  dump(alpha/'sequence.json',{'canvas':[286,508],'fps':30,'frames':rows,'alpha':'straight RGBA; no raw/reference pixels in subtitle'})
  result=subprocess.run(['ffmpeg','-v','error','-i',str(fp),'-f','null','-'],capture_output=True);assert result.returncode==0
  state='trial-encoded-frame-reviewed-not-user-approved';technical={'fullDecode':True,'frameCount':count,'sha256':sha(fp),'audioListeningApproved':False,'continuousVisualReview':False}
 limitations=['原字体身份仍未确认；字体为候选近似','新口播字词时间尚未人工听审，语义时点为机器识别候选']
 if id=='cg17':limitations+=['人物前景使用新片固定头部GrabCut，肩/手区域遮挡未建立通用抠像','巨字斜度、阴影及重复横向相位仍待用户复审']
 if id=='cg18':limitations+=['短语板文字已按新内容调整，字级时钟为按参考顺序重定时','原片右板出现晚于左板，当前保留该接力关系']
 if id=='cg19':limitations+=['第一句滑入与第二句压缩模糊沿用已有t15实现，原字体及推进曲线仍待确认']
 record={'occurrence':id,'name':c['name'],'file':rel(fp),'referenceFile':f'observations/accepted-review/{id}/reference-clip.mp4','recipe':rel(rp),'input':rel(inp),'frameCount':c['frameCount'],'rawRange':c['rawRange'],'sourceRange':c['sourceRange'],'visualFamily':c['visualFamily'],'subtitleFamily':c['subtitleFamily'],'verificationState':state,'limitations':limitations,'verification':technical,'mediaSha256':sha(fp)}
 manifest.append(record);dump(R/(id+'-verification.json'),record);print(id+' ready',flush=True)
dump(O/'manifest.json',{'stage':'03-pilot','accepted':False,'groups':manifest,'familyImplementationPolicy':'one canonical implementation per visual/subtitle family; occurrence recipes reference it'})
