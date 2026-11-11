import sys,json,hashlib,subprocess,copy
from pathlib import Path
P=Path(__file__).resolve().parents[4];sys.path.insert(0,str(P/'source/pilot'))
from PIL import Image,ImageDraw
from components import scene_batch as impl
from components.common import load,core
S=P/'source/pilot/batches/scene';O=P/'render/pilot/batches/scene';R=P/'reviews/batches/scene'
for p in [S,O,R]:p.mkdir(parents=True,exist_ok=True)
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(P)).replace('\\','/')
A='source/pilot/batches/scene/assets/'
manifest=load(P/'source/pilot/new-input/manifest.json');src=manifest['path']
specs=[
 {'occurrence':'cg04','name':'城市语境与斜切案例接力','sourceRange':[174,300],'rawRange':[14.466667,19.5],'visualFamily':'v03','subtitleFamily':'t03','assets':{'background':A+'city.jpg','example':A+'desk.jpg'},'text':{'context':'生意风光','change':'风险自担','result':'亏损难翻身'},'clock':{'context':0,'change':35,'diagonalIn':[69,115],'result':98,'returnStart':141,'returnEnd':147},'purpose':'生意看着风光，风险实际由自己承担；城市场景铺垫，斜切工作案例接管，再回人物。'},
 {'occurrence':'cg07','name':'人物缩入圆窗与双卡对比','sourceRange':[367,450],'rawRange':[5.833333,9.566667],'visualFamily':'v05','subtitleFamily':'t05','assets':{'left':A+'desk.jpg','right':A+'meeting.jpg'},'text':{'title':'想做又不敢','left':'怕亏本','right':'怕闲话'},'clock':{'presenterShrink':[0,22],'title':25,'leftCard':[35,47],'rightCard':[69,81],'leftLabel':39,'rightLabel':73},'purpose':'人物先让位，先讲亏本顾虑，再讲社会评价顾虑；双卡并列表示两类阻力。'},
 {'occurrence':'cg08','name':'数字雨与叠层案例面板','sourceRange':[462,531],'rawRange':[24.466667,29.333333],'visualFamily':'v06','subtitleFamily':'t06','assets':{'top':A+'office.jpg','second':A+'laptop.jpg'},'text':{'first':'别陷在焦虑里','second':'学个落地本事'},'clock':{'firstText':0,'secondPanel':[71,93],'secondText':76},'purpose':'焦虑与空想先作为上层问题，学习具体技能的行动作为第二面板推进；下方真人维持口播。'},
 {'occurrence':'cg09','name':'横线案例窗与人物圆窗','sourceRange':[531,598],'rawRange':[34.433333,37.566667],'visualFamily':'v07','subtitleFamily':None,'assets':{'example':A+'desk.jpg'},'text':{},'clock':{},'captions':[{'in':0,'out':52,'text':'别人踩过的坑提前了解'},{'in':52,'out':94,'text':'少走很多弯路'}],'purpose':'案例窗承担经验学习语境，圆窗人物负责解释，普通口播字幕不登记为字幕动效。'}]
for c in specs:
 c['frameCount']=round((c['rawRange'][1]-c['rawRange'][0])*30);c['fontRoles']={'body':{'path':('C:/Windows/Fonts/Noto Sans SC Bold (TrueType).otf' if c['occurrence']=='cg08' else impl.FONT),'identity':'candidate only; source font not established','shadow':'shared-text-style.json'}}
 c['fontRoles']['statement']={'path':'C:/Windows/Fonts/Noto Sans SC Bold (TrueType).otf','identity':'candidate condensed source-like sans'};c['fontRoles']['labels']={'path':impl.FONT,'identity':'candidate only'};c['inputSHA']=manifest['sha256'];save(S/(c['occurrence']+'-input.json'),c)
 order={'v03':['background','presenter','example','tornEdge'],'v05':['background','presenter','leftCard','rightCard'],'v06':['background','topPanel','secondPanel','presenter'],'v07':['background','example','presenter','ordinaryCaption']}[c['visualFamily']]
 if c['visualFamily']=='v03':order+=['returnPresenter']
 refs={'visual':{'id':c['visualFamily'],'entrypoint':'components.scene_batch:render','source':'source/pilot/components/scene_batch.py','sha256':sha(P/'source/pilot/components/scene_batch.py')}}
 if c['subtitleFamily']:refs['subtitle']={'id':c['subtitleFamily'],'entrypoint':'components.scene_batch:render_subtitle','source':'source/pilot/components/scene_batch.py','sha256':sha(P/'source/pilot/components/scene_batch.py')}
 recipe={'schema':1,'id':'complete-'+c['occurrence'],'status':'pilot-source-draft','occurrence':c['occurrence'],'input':rel(S/(c['occurrence']+'-input.json')),'components':refs,'layerOrder':['visual.'+x for x in order]+(['subtitle.text'] if c['subtitleFamily'] else []),'commonSha256':sha(P/'source/pilot/components/common.py'),'sharedStyle':'source/pilot/complete01-02/shared-text-style.json','sharedStyleSha256':sha(P/'source/pilot/complete01-02/shared-text-style.json'),'clock':{'fps':30,'frameOrigin':0},'verificationState':'trial','completeGroupValidated':False,'supportBindings':{'source/pilot/t04_render.py':sha(P/'source/pilot/t04_render.py')}}
 save(S/(c['occurrence']+'-recipe.json'),recipe)

(S/'PURPOSE.md').write_text('# 场景编排批次｜03 试作\n\n'+ '\n\n'.join('## '+c['occurrence']+' '+c['name']+'\n'+c['purpose']+'\n来源帧 '+str(c['sourceRange'])+'；新口播 '+str(c['rawRange'])+'。画面组件 '+c['visualFamily']+'，字幕组件 '+str(c['subtitleFamily'])+'。' for c in specs)+'\n\n所有照片是示意实拍素材，不是收入、投资或亏损事实证据。不能用于需要真实账单、收益凭证的句子。图片插槽可换，人物圆窗须按新人物重新裁切；v06 当前 GrabCut 只测本输入，不声称任意抠像。关键时钟均为参数；叠卡不得挡住人物脸，双卡标题不得超出卡宽。退出遵循参考交接：cg07→cg08、cg08→cg09硬切，cg04内部返回人物。\n',encoding='utf-8')

def encode(c):
 id=c['occurrence'];N=c['frameCount'];start=c['rawRange'][0];out=O/(id+'.mp4')
 dec=subprocess.Popen(['ffmpeg','-v','error','-ss',str(start),'-i',src,'-frames:v',str(N),'-vf','fps=30,scale=286:508','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
 enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-s','286x508','-pix_fmt','rgb24','-r','30','-i','pipe:0','-ss',str(start),'-i',src,'-map','0:v','-map','1:a:0','-t',str(N/30),'-vf','scale=628:1118:flags=lanczos','-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(out)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
 proof=[];recipe=load(S/(id+'-recipe.json'))
 for n in range(N):
  b=dec.stdout.read(286*508*3)
  if len(b)!=286*508*3:raise ValueError('missing raw frame '+str(n))
  raw=Image.frombytes('RGB',(286,508),b);layers={'visual.'+k:v for k,v in impl.render(c['visualFamily'],raw,n,c).items()}
  if c['subtitleFamily']:layers.update({'subtitle.'+k:v for k,v in impl.render_subtitle(c['subtitleFamily'],n,c).items()})
  frame=Image.new('RGBA',(286,508))
  for k in recipe['layerOrder']:
   if k in layers:frame.alpha_composite(layers[k])
  enc.stdin.write(frame.convert('RGB').tobytes())
  if n in {0,round(N*.2),round(N*.45),round(N*.7),N-1}:
   frame.save(R/(id+f'-{n:03d}.png'));proof.append(n)
   for name,im in layers.items():
    if name.startswith('subtitle.') or name.endswith('presenter'):im.save(R/(id+'-'+name.replace('.','-')+f'-{n:03d}.png'))
 enc.stdin.close();err=enc.stderr.read();rc=enc.wait();dec.wait()
 if rc:raise RuntimeError(err.decode())
 # Validate actual encoded stream, not in-memory renders.
 result=subprocess.run(['ffmpeg','-v','error','-i',str(out),'-map','0:v:0','-f','null','-'],capture_output=True)
 assert result.returncode==0,result.stderr
 cv=__import__('cv2');cap=cv.VideoCapture(str(out));assert round(cap.get(cv.CAP_PROP_FRAME_COUNT))==N
 sheet=Image.new('RGB',(286*5,540),'#101418');draw=ImageDraw.Draw(sheet)
 for k,n in enumerate(proof):
  cap.set(cv.CAP_PROP_POS_FRAMES,n);ok,a=cap.read();assert ok;im=Image.fromarray(cv.cvtColor(a,cv.COLOR_BGR2RGB)).resize((286,508));sheet.paste(im,(286*k,28));draw.text((286*k+5,8),f'new f{n}',fill='white')
 cap.release();sheet.save(R/(id+'-encoded-process.jpg'))
 return {'occurrence':id,'name':c['name'],'file':rel(out),'referenceFile':f'observations/accepted-review/{id}/reference-clip.mp4','recipe':rel(S/(id+'-recipe.json')),'input':rel(S/(id+'-input.json')),'frameCount':N,'rawRange':c['rawRange'],'sourceRange':c['sourceRange'],'visualFamily':c['visualFamily'],'subtitleFamily':c['subtitleFamily'],'verificationState':'trial','sha256':sha(out),'technical':{'fullDecode':True,'frameCount':N,'sourceFamilyDeduplicated':True},'proofFrames':proof,'limitations':['原字体身份未确认；候选字形、字距及动画仍需对标返工和用户复审','照片为新口播示意素材，不是财务事实证据；与原片材质不同','新口播词时钟基于ASR假设，未完成听审','当前为03完整组合候选，不代表正式库通过']+(['v06人物抠像边缘为GrabCut试作，手指与头发局部需人工精修'] if id=='cg08' else [])}
if __name__=='__main__':
 groups=[]
 for c in specs:
  print('Rendering',c['occurrence'],flush=True);g=encode(c);groups.append(g);save(O/'manifest.json',{'status':'03-trial','groups':groups})
 print('complete',len(groups),flush=True)
