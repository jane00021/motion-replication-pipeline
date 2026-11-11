from pathlib import Path
import sys,copy,subprocess,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import t04_render as core
from components.common import *
from components.closing_batch import render_subtitle
from components.runtime import compose,validate_recipe
from components.pairing import check
S=P/'source/pilot/last-four/closing';O=P/'render/pilot/last-four/closing';R=P/'reviews/last-four/closing';rawPath=load(P/'source/pilot/new-input/manifest.json')['path']
base=copy.deepcopy(load(P/'source/pilot/t04/input-A.json')['roles']['body']);base.update(size=26,fill='#f8f8f5');base['shadow'].update(dx=1.,dy=1.4,blur=.55,opacity=.9)
same={'profile':'t15-calibrated-v2','frames':46,'fps':30,'styles':{'first':copy.deepcopy(base),'second':copy.deepcopy(base)},'phrases':{'first':{'text':'才是普通人','align':'left','anchor':29,'y':336,'entry':1,'settle':9},'second':{'text':'该走的路','align':'right','anchor':246,'y':375,'entry':25,'settle':30,'entryBlur':2.4,'travelX':25,'travelY':10}},'eventEvidence':'reference first local1..9; second local25..30; last45 still visible'}
same['styles']['first']['size']=25.5
new=copy.deepcopy(same);new.update(frames=78);new['phrases']['first']['text']='一步一步来';new['phrases']['first']['entry']=1;new['phrases']['first']['settle']=10;new['phrases']['second'].update(text='生活慢慢变好',entry=37,settle=45)
# Same ink-based font size retained for six-character new conclusion, right anchor controls layout.
params={'occurrence':'cg19','frames':78,'rawRange':[41.2,43.8],'subtitle':new,'expression':'一步一步来是做法；生活慢慢变好是结果。前句先读，后句接力；无强行着色、无退出。'}
core.dump(S/'input-same.json',{'subtitle':same});core.dump(S/'input.json',params)
refs={'visual':{'id':None,'entrypoint':'components.runtime:passthrough','source':'source/pilot/components/runtime.py'},'subtitle':{'id':'t15','entrypoint':'components.closing_batch:render_subtitle','source':'source/pilot/components/closing_batch.py'}}
for ref in refs.values():ref['sha256']=core.file_sha(P/ref['source'])
recipe={'occurrence':'cg19','id':'cg19-last-four','verificationState':'trial','completeGroupValidated':False,'components':refs,'input':'source/pilot/last-four/closing/input.json','layerOrder':['visual.presenter','subtitle.text'],'sharedStyle':'source/pilot/complete01-02/shared-text-style.json','commonSha256':core.file_sha(P/'source/pilot/components/common.py'),'sharedStyleSha256':core.file_sha(P/'source/pilot/complete01-02/shared-text-style.json'),'supportBindings':{p:core.file_sha(P/p) for p in ['source/pilot/round2_render.py','source/pilot/t04_render.py','source/pilot/components/detail_tools.py']}}
core.dump(S/'recipe.json',recipe);validate_recipe(recipe);check(recipe,params,P)
fontrecord={k:{'path':v['path'],'face':v['face'],'sha256':core.file_sha(v['path']),'size':v['size'],'shadow':v['shadow'],'sameWordInk':core.ink(same['phrases'][k]['text'],v)[1],'newWordInk':core.ink(new['phrases'][k]['text'],v)[1]} for k,v in new['styles'].items()};core.dump(R/'roles-font-layout.json',fontrecord)
def render_case(name,c,withraw=False):
 count=c['subtitle']['frames'];folder=O/name;folder.mkdir(exist_ok=True);adir=folder/'rgba';adir.mkdir(exist_ok=True);path=O/(name+'.mp4')
 dec=None
 if withraw:
  dec=subprocess.Popen(['ffmpeg','-v','error','-threads','2','-ss','41.2','-i',rawPath,'-t',str(count/30),'-vf','fps=30,scale=286:508','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
  aud=folder/'audio.wav';subprocess.run(['ffmpeg','-v','error','-y','-ss','41.2','-i',rawPath,'-t',str(count/30),'-vn','-ac','1',str(aud)],check=True)
 extra=['-i',str(aud),'-c:a','aac','-shortest'] if withraw else ['-an']
 enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','286x508','-r','30','-i','pipe:0']+extra+['-c:v','libx264','-threads','2','-crf','14','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],stdin=subprocess.PIPE)
 rows=[]
 for n in range(count):
  sub=render_subtitle('t15',n,c)['text'];sub.save(adir/f'{n:04d}.png');rows.append({'frame':n,'alphaBBox':sub.getchannel('A').getbbox()})
  if dec:raw=Image.frombytes('RGB',(286,508),dec.stdout.read(286*508*3)).convert('RGBA');out=compose(recipe,raw,n,c)
  else:out=Image.new('RGBA',(286,508),'#27333c');out.alpha_composite(sub)
  enc.stdin.write(out.convert('RGB').tobytes())
 enc.stdin.close();assert enc.wait()==0
 if dec:assert dec.wait()==0
 core.dump(adir/'sequence.json',{'fps':30,'canvas':[286,508],'alpha':'true RGBA','frames':rows,'finalFrameVisibleAsReference':rows[-1]['alphaBBox'] is not None});assert rows[-1]['alphaBBox']
 subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'],check=True)
 return path
samepath=render_case('same-word',{'subtitle':same});newpath=render_case('complete-applied',params,True)
# Rebind after rendering to parent-owned runtime only if unchanged; no silent overwrite shared modules.
row={'occurrence':'cg19','name':'收尾双句错位接力·字形与时钟校准','file':str(newpath.relative_to(P)).replace('\\','/'),'referenceFile':'observations/accepted-review/cg19/reference-clip.mp4','input':'source/pilot/last-four/closing/input.json','recipe':'source/pilot/last-four/closing/recipe.json','frameCount':78,'rawRange':[41.2,43.8],'sourceRange':[1172,1218],'sourceRangeUnit':'zero-based frames, end exclusive','visualFamily':None,'subtitleFamily':'t15','sha256':core.file_sha(newpath),'mediaSha256':core.file_sha(newpath),'verificationState':'trial-encoded-not-user-approved','limitations':['原字体为思源宋体Heavy候选，未确认原字体身份','新口播37帧接力来自机器语音候选，尚未人工听审','原片第二句动态模糊与压缩具体曲线仍近似','本轮仅cg19，不改变其他已认可媒体']}
core.dump(O/'manifest.json',{'groups':[row],'stageAccepted':False})
# Real encoded outputs compared at equal local clock for same-word, and explicit phase times for migration.
def decoded(path,n):
 a=subprocess.run(['ffmpeg','-v','error','-ss',str(n/30),'-i',str(path),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],capture_output=True,check=True).stdout;return Image.frombytes('RGB',(286,508),a)
fs=[0,1,3,6,9,24,25,27,30,45];board=Image.new('RGB',(286*10,540*2));d=ImageDraw.Draw(board)
for i,n in enumerate(fs):
 board.paste(Image.open(P/f'observations/frame-audit/frames/{1172+n+1:04d}.jpg'),(i*286,0));board.paste(decoded(samepath,n),(i*286,540));d.text((i*286+2,510),f'source local{n}',fill='white');d.text((i*286+2,1050),f'encoded same local{n}',fill='white')
board.save(R/'same-clock-encoded-comparison.jpg')
board=Image.new('RGB',(286*6,540*2));d=ImageDraw.Draw(board)
for i,(sn,nn) in enumerate([(1,1),(9,10),(24,36),(25,37),(30,45),(45,77)]):
 board.paste(Image.open(P/f'observations/frame-audit/frames/{1172+sn+1:04d}.jpg'),(i*286,0));board.paste(decoded(newpath,nn),(i*286,540));d.text((i*286+2,510),f'source local{sn}',fill='white');d.text((i*286+2,1050),f'new local{nn} phase matched',fill='white')
board.save(R/'new-content-phase-comparison.jpg')
# Independent edit/shadow/material interventions, without touching actual approved media.
a=render_subtitle('t15',45,params)['text'];assert render_subtitle('t15',45,params,['text'])=={}
changed=copy.deepcopy(params);changed['subtitle']['phrases']['second']['text']='未来慢慢变好';b=render_subtitle('t15',45,changed)['text'];assert np.any(np.array(a)!=np.array(b))
shadowoff=copy.deepcopy(params)
for v in shadowoff['subtitle']['styles'].values():v['shadow']['opacity']=0
b=render_subtitle('t15',45,shadowoff)['text'];shadowdiff=int(np.any(np.array(a)!=np.array(b),axis=2).sum());assert shadowdiff>0
core.dump(R/'verification.json',{'frameCount':78,'sameWordFrames':46,'fullDecode':True,'textEditable':True,'disabledTextTransparent':True,'shadowChangesPixelCount':shadowdiff,'finalAlphaVisible':True,'outOfBoundsInk':False,'rawRange':[41.2,43.8],'encodedSha256':core.file_sha(newpath),'sameWordSha256':core.file_sha(samepath),'sourceHash':core.file_sha(P/'source/pilot/round2_render.py'),'scope':'same local clock encoded comparison for reference words; explicitly mapped phase clocks for new content','continuousVisualWatch':False,'audioListening':False,'stageAccepted':False})
print(json.dumps(row,ensure_ascii=False))
