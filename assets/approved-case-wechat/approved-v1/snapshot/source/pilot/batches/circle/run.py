"""Batch orchestration only: all family implementations live in circle_batch.py."""
from pathlib import Path
import sys,json,hashlib,subprocess,copy,argparse
P=Path(__file__).resolve().parents[4];sys.path.insert(0,str(P/'source/pilot'))
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from components import circle_batch as component
from components import runtime
S=P/'source/pilot/batches/circle';O=P/'render/pilot/batches/circle';R=P/'reviews/batches/circle'
for p in [S,O,R]:p.mkdir(parents=True,exist_ok=True)
SRC=json.loads((P/'source/pilot/new-input/manifest.json').read_text('utf-8'))['path']
REF='C:/Users/Administrator/文档/xwechat_files/wxid_rfsxn410awad12_0c48/msg/video/2026-11/0a5c43a3ed077659fe8c5fe93110cc00.mp4'
def dump(path,c):Path(path).write_text(json.dumps(c,ensure_ascii=False,indent=2),'utf-8')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
SPECS={
 'cg10':{'name':'数量揭晓与主题重排','family':'t08','source':[617,670],'raw':[11.52,12.52],
  'same':{'left':'三','right':'个','subject':'财经底线'},'new':{'left':'三','right':'个','subject':'提醒'},'events':{'quantity':0,'reflow':30,'subject':31,'exitStart':48,'clear':52},
  'purpose':'数量先建立预期，再让出中间位置给主题；新口播用“所以我想劝一下”引出随后风险、技能和耐心三个提醒。三个是编辑概括，非逐字转录。'},
 'cg11':{'name':'序号一与撕纸双句接力','family':'t09','source':[669,744],'raw':[12.52,14.46],
  'same':{'number':'1','tag':'#理性购物','first':'降掉无效消费','second':'戒掉冲动购物'},'new':{'number':'1','tag':'#先看风险','first':'别脑子一热','second':'就去开店投资'},'events':{'number':4,'tag':11,'first':9,'second':48},'backing':True,
  'purpose':'序号和标签识别第一条规则，撕纸主句先落定，第二句补足具体行为。迁移为谨慎开店投资，保持先提醒后展开。'},
 'cg12':{'name':'概念分清与两端问号对照','family':'t10','source':[755,803],'raw':[22.54,24.48],
  'same':{'title':'分清楚','question':'？','left':'想要','right':'需要'},'new':{'title':'分清楚','question':'？','left':'体力','right':'思路'},'events':{'title':1,'question':3,'left':17,'right':29},
  'purpose':'标题先声明区分任务，中心问号形成比较，两端概念错时出现；新口播区分体力与思路，不把重点固定在源字。'},
 'cg13':{'name':'序号二与例图结论接力','family':'t09','source':[804,868],'raw':[26.82,29.34],
  'same':{'number':'2','tag':'#本金为先','first':'守住本金','second':'永远优先'},'new':{'number':'2','tag':'#本事落地','first':'与其空想','second':'学个能落地的本事'},'events':{'number':2,'tag':9,'first':10,'second':37,'exitStart':58,'clear':63},'firstColor':'#a00c27','firstSize':33,'firstX':59,'firstY':311,'secondX':68,'secondY':325,'secondSize':25,'evidence':True,'replaceFirst':True,
  'purpose':'与第一条共用序号与标签机制，用图片支撑新规则，红色先句再由白色结论接管。迁移例图改为键盘操作实拍，表达学本事；不复用不相干的钞票。'},
 'cg14':{'name':'金属警示与风险重点接管','family':'t11','source':[917,952],'raw':[29.34,32.06],
  'same':{'warning':'暗藏风险','prefix':'市面上','context':'夸大收益理财'},'new':{'warning':'警惕速成','prefix':'别相信','context':'快速赚钱'},'events':{'warning':4,'warningText':6,'context':-5,'exitStart':31,'clear':34},
  'purpose':'支撑语境先维持阅读，金属警示符号在人物后侧放大，红色风险判断接管；新口播明确警惕短期快速赚钱。'},
 'cg15':{'name':'中心提醒与双分支展开','family':'t12','source':[960,1005],'raw':[38.82,40.52],
  'same':{'lead':'普通人要远离','left':'投机','right':'炒作'},'new':{'lead':'踏实比求快更重要','left':'踏实','right':'求快'},'events':{'lead':-5,'leftArrow':13,'left':18,'rightArrow':23,'right':29},
  'purpose':'中心句先提出判断，两条箭头先后展开对照对象。迁移强调踏实与求快，不声称二者都是应远离的对象。'},
 'cg16':{'name':'序号三与标签定位','family':'t09','source':[1008,1047],'raw':[40.52,43.8],
  'same':{'number':'3','tag':'#减少负债','first':'','second':''},'new':{'number':'3','tag':'#一步一步来','first':'','second':''},'events':{'number':2,'tag':8},'markerOnly':True,
  'purpose':'序号三定位第三条并用短标签概括；本次完整 occurrence 本就没有前两条的主句层。迁移标签概括“选对方式，一步一步来”，不重复实现序号机制。'}
}
def configs(id,spec):
 duration=round((spec['raw'][1]-spec['raw'][0])*30);sf=spec['source'][1]-spec['source'][0]
 same={'id':id+'-same-text','occurrence':id,'frames':sf,'fps':30,'subtitleFamily':spec['family'],'referenceFrames':spec['source'],'visual':{'window':[66,87,154,154],'presenterCrop':[67,88,219,240]},'subtitle':{'text':spec['same'],'events':spec['events']}}
 for key in ['backing','firstColor','firstSize','firstX','firstY','secondX','secondY','secondSize','markerOnly','replaceFirst']:
  if key in spec:same['subtitle'][key]=spec[key]
 if spec.get('evidence'):
  same['visual']['evidence']={'path':'source/pilot/complete01-02/assets/work-keyboard.jpg','start':10,'end':63,'xy':[34,263],'size':[218,155]}
  same['limitation']='原钞票独立素材缺失：同字候选采用键盘照片仅检查例图插槽，不能作为原素材基准验收。'
 c=copy.deepcopy(same);c.update(id=id+'-unedited-migration',frames=duration,rawRange=spec['raw']);c['visual']['presenterCrop']=[31,82,255,306];c['subtitle']['text']=spec['new']
 # New footage keeps its own tempo; map reference event phases to the local clock.
 c['subtitle']['events']={k:round(v*duration/sf) for k,v in spec['events'].items()}
 # Speech roles override proportional phase mapping where the new clause hands off earlier.
 if id=='cg11':c['subtitle']['events'].update(number=0,tag=3,first=2,second=24)
 if id=='cg12':c['subtitle']['events'].update(title=1,question=4,left=7,right=32)
 if id=='cg13':c['subtitle']['events'].update(number=0,tag=4,first=5,second=24)
 if spec.get('evidence'):
  c['visual']['evidence'].update(start=round(10*duration/sf),end=duration-1)
  # Longer new conclusion must retain readability; fit actual glyph width in same envelope.
  c['subtitle'].update(secondSize=23,secondX=52,secondY=353)
 c['semanticBindings']={'purpose':spec['purpose'],'textSource':'人工选取本地ASR候选，未独立听审；同义概括已在purpose说明','unchangedMechanism':spec['family'],'reviewStatus':'trial'}
 return same,c
def recipe(id,c):
 path='source/pilot/components/circle_batch.py';code=sha(P/path)
 return {'schema':1,'id':id+'-circle-draft','occurrence':id,'status':'pilot-source-draft','input':str((S/f'{id}-input.json').relative_to(P)).replace('\\','/'),'components':{'visual':{'id':'v04','entrypoint':'components.circle_batch:render','source':path,'sha256':code},'subtitle':{'id':c['subtitleFamily'],'entrypoint':'components.circle_batch:render_subtitle','source':path,'sha256':code}},'commonSha256':sha(P/'source/pilot/components/common.py'),'sharedStyle':'source/pilot/complete01-02/shared-text-style.json','sharedStyleSha256':sha(P/'source/pilot/complete01-02/shared-text-style.json'),'supportBindings':{'source/pilot/t04_render.py':sha(P/'source/pilot/t04_render.py')},'clock':{'fps':30,'frameOrigin':0,'eventsFromInput':'subtitle.events'},'layerOrder':['visual.background','subtitle.backMark','visual.presenterWindow','visual.evidence','subtitle.foregroundText'],'completeGroupValidated':False,'verificationState':'trial','purposeDocument':'source/pilot/batches/circle/PURPOSE.md'}
def encoded(id,c,source,start,output,save_alpha=False):
 cap=cv2.VideoCapture(source);cap.set(cv2.CAP_PROP_POS_FRAMES,round(start*30));nframes=c['frames'];alpha=[]
 command=['ffmpeg','-v','error','-y','-threads','1','-f','rawvideo','-pix_fmt','rgb24','-s','286x508','-r','30','-i','pipe:0','-threads','1','-ss',str(start),'-i',str(source),'-map','0:v','-map','1:a:0','-c:v','libx264','-threads','1','-crf','16','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-t',str(nframes/30),'-shortest','-movflags','+faststart',str(output)]
 proc=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE);folder=O/id/'rgba';folder.mkdir(parents=True,exist_ok=True)
 rec=recipe(id,c);runtime.validate_recipe(rec)
 for n in range(nframes):
  ok,a=cap.read()
  if not ok:raise RuntimeError('source exhausted '+id)
  raw=Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).resize((286,508),Image.Resampling.LANCZOS)
  im=runtime.compose(rec,raw,n,c);proc.stdin.write(im.convert('RGB').tobytes())
  if save_alpha:
   layers=component.render_subtitle(c['subtitleFamily'],n,c)
   # Two transparent slots remain separate so title/number can stay behind person.
   for slot in ['backMark','foregroundText']:layers[slot].save(folder/f'{n:04d}-{slot}.png')
   alpha.append({'frame':n,'backMarkBBox':layers['backMark'].getchannel('A').getbbox(),'foregroundTextBBox':layers['foregroundText'].getchannel('A').getbbox()})
 proc.stdin.close();err=proc.stderr.read();rc=proc.wait();cap.release()
 if rc:raise RuntimeError(err.decode())
 if save_alpha:dump(folder/'sequence.json',{'fps':30,'size':[286,508],'slots':['backMark','foregroundText'],'format':'straight RGBA PNG','frames':alpha,'componentSourceSha256':sha(P/'source/pilot/components/circle_batch.py')})
 return {'sha256':sha(output),'frameCount':nframes}
def board(id,c,same):
 source=SPECS[id]['source'];cols=7;cw=170;sheet=Image.new('RGB',(cols*cw,860),'#eeeeea');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',12)
 cap=cv2.VideoCapture(str(O/id/'result.mp4'));sc=cv2.VideoCapture(str(O/id/'same-text-candidate.mp4'))
 # Source and same-text use exact same local frame. New result aligned by phase, not mislabeled common clock.
 for j,f in enumerate(np.linspace(0,source[1]-source[0]-1,cols,dtype=int)):
  original=Image.open(P/'observations/frame-audit/frames'/f'{source[0]+f+1:04d}.jpg').resize((143,254))
  sc.set(cv2.CAP_PROP_POS_FRAMES,int(f));ok,a=sc.read();cand=Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).resize((143,254))
  sheet.paste(original,(j*cw,20));sheet.paste(cand,(j*cw,300));d.text((j*cw,0),f'原参考 local f{f}',font=font,fill='#111111');d.text((j*cw,280),f'同字候选 local f{f}',font=font,fill='#111111')
  local=round(f/max(1,same['frames']-1)*(c['frames']-1));cap.set(cv2.CAP_PROP_POS_FRAMES,local);ok,a=cap.read();new=Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).resize((143,254));sheet.paste(new,(j*cw,580))
  d.text((j*cw,560),f'迁移阶段 f{local}',font=font,fill='#111111')
 sc.release();cap.release();sheet.save(R/f'{id}-source-same-migration.jpg',quality=92)
def qa(path):
 cap=cv2.VideoCapture(str(path));count=0;dark=0
 while True:
  ok,a=cap.read()
  if not ok:break
  count+=1;dark+=int(a.mean()<1)
 cap.release();return {'fullDecode':True,'decodedFrames':count,'blackFrames':dark,'sha256':sha(path),'continuousVisualPlayback':False,'listening':False}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--group');ap.add_argument('--skip-same',action='store_true');args=ap.parse_args();rows=[]
 for id,spec in SPECS.items():
  if args.group and id!=args.group:continue
  same,c=configs(id,spec);folder=O/id;folder.mkdir(exist_ok=True)
  dump(S/f'{id}-input.json',c);dump(S/f'{id}-same-text.json',same);dump(S/f'{id}-recipe.json',recipe(id,c))
  if not args.skip_same:encoded(id,same,REF,spec['source'][0]/30,folder/'same-text-candidate.mp4')
  result=encoded(id,c,SRC,spec['raw'][0],folder/'result.mp4',True);board(id,c,same);check=qa(folder/'result.mp4');dump(R/f'{id}-technical.json',check)
  row={'occurrence':id,'name':spec['name'],'file':str((folder/'result.mp4').relative_to(P)).replace('\\','/'),'referenceFile':f'observations/accepted-review/{id}/reference-clip.mp4','recipe':f'source/pilot/batches/circle/{id}-recipe.json','input':f'source/pilot/batches/circle/{id}-input.json','frameCount':c['frames'],'rawRange':spec['raw'],'sourceRange':[v/30 for v in spec['source']],'sourceFrames':spec['source'],'visualFamily':'v04','subtitleFamily':spec['family'],'variant':id,'verificationState':'trial','sha256':result['sha256'],'limitations':['原字体未确认：使用思源宋体Heavy候选；数字Impact斜切材质与参考原轮廓仍有差异','原声效未独立复刻，仅保留新口播音轨；字词时钟待实际听审','本轮仅同钟/阶段抽帧和完整解码，未声称连续视觉播放或用户认可']+(['例图采用键盘实拍替代钞票；原素材候选不具备原图基准验收资格'] if spec.get('evidence') else []),'comparisonEvidence':f'reviews/batches/circle/{id}-source-same-migration.jpg','purpose':spec['purpose']}
  rows.append(row);dump(R/'partial-manifest.json',{'groups':rows,'status':'03-pilot-trial-not-accepted'});print(id,result['sha256'],flush=True)
 dump(O/'manifest.json',{'schema':1,'status':'03-pilot-trial-not-accepted','groups':rows,'componentImplementations':{'visual':['v04'],'subtitle':['t08','t09','t10','t11','t12']},'occurrenceFamilyMap':{id:{'visual':'v04','subtitle':s['family']} for id,s in SPECS.items()},'deduplication':'cg11/cg13/cg16 reference the same t09 implementation; every group references v04; all review states independent'})
if __name__=='__main__':main()
