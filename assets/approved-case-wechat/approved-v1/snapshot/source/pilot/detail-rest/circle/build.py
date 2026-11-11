from pathlib import Path
import sys,json,copy,hashlib,subprocess,importlib.util
P=Path(__file__).resolve().parents[4];sys.path.insert(0,str(P/'source/pilot'))
from components.common import *
from components.runtime import compose,validate_recipe
from components.circle_batch import render_subtitle
from components.detail_tools import glyph_tile
from playwright.sync_api import sync_playwright
S=P/'source/pilot/detail-rest/circle';O=P/'render/pilot/detail-rest/circle';R=P/'reviews/detail-rest/circle'
for p in [S,O,R]:p.mkdir(parents=True,exist_ok=True)
SRC=load(P/'source/pilot/new-input/manifest.json')['path'];REF='C:/Users/Administrator/文档/xwechat_files/wxid_rfsxn410awad12_0c48/msg/video/2026-11/0a5c43a3ed077659fe8c5fe93110cc00.mp4'
FONTS=load(P/'source/pilot/detail-two/fonts.json');IDS=['cg10','cg11','cg12','cg14','cg15','cg16']
spec=importlib.util.spec_from_file_location('old_circle_run',P/'source/pilot/batches/circle/run.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,c):Path(p).write_text(json.dumps(c,ensure_ascii=False,indent=2),'utf-8')
def role(font,w,h,x,y,fill='#fffef7',align='center',**more):
 return dict(path=FONTS.get(font,font),size=48,inkWidth=w,inkHeight=h,anchorX=x,inkY=y,fill=fill,align=align,outlinePx=0,shadow={'dx':.85,'dy':1.3,'blur':.4,'opacity':.85},**more)
def configure(id,same):
 old_same,c=old.configs(id,old.SPECS[id]);c=old_same if same else c;c=copy.deepcopy(c);c['detailRest']=True;c['detailProfile']='measured-ink-roles-svg-v1';c['visual']['presenterCrop']=[67,88,219,240] if same else [31,76,255,300];t=c['subtitle']['text'];e=c['subtitle']['events']
 if id=='cg10':
  c['typeRoles']={'left':role('serif-heavy',84,79,87,280,reflowXY=[52,241]),'right':role('serif-heavy',84,87,184,276,reflowXY=[236,314]),'subject':role('serif-heavy',145 if same else 69,31,137,307,'#aa0021',entryDx=12)}
  if not same:c['rawRange']=[11.52,14.46];c['frames']=88;c['subtitle']['events']={'quantity':0,'reflow':26,'subject':29,'exitStart':79,'clear':87}
 elif id in ('cg11','cg16'):
  c['numberRole']=role('C:/Windows/Fonts/arialbi.ttf',74 if id=='cg11' else 93,119,36 if id=='cg11' else 28,43)
  c['tagRole']=role('serif-heavy',76 if same else (76 if id=='cg11' else 85),14,216,234)
  c['typeRoles']={'first':role('serif-heavy',151 if same else 139,25 if same else 30,110,309,align='center',entryDx=22),'second':role('serif-bold',153 if same else 160,25 if same else 29,205 if same else 185,354,align='center',entryDx=20)}
  if id=='cg11':
   c['tornAsset']='source/pilot/detail-rest/circle/assets/torn-paper.png';c['typeRoles']['second']['anchorX']=196 if same else 184
   if same:c['subtitle']['events'].update(first=13,second=49)
 elif id=='cg12':
  c['subtitle']['text']['question']='?'
  c['typeRoles']={'title':role('serif-heavy',191,67,139,38,entryDx=0),'question':role('C:/Windows/Fonts/timesbd.ttf',42,73,143,285,'#b60025'),'left':role('serif-bold',62,29,72,277,entryDx=-24),'right':role('serif-bold',66,29,225,334,entryDx=24)}
 elif id=='cg14':
  c['warningAsset']='source/pilot/detail-rest/circle/assets/warning-red.png';c['warningSvg']='source/pilot/detail-rest/circle/assets/warning-red.svg'
  c['typeRoles']={'warning':role('serif-heavy',181,37,139,235 if same else 245,'#a60024'),'prefix':role('serif-bold',49,20,59,317),'context':role('serif-bold',155 if same else 112,26,168 if same else 151,309,'#dac565')}
 elif id=='cg15':
  c['typeRoles']={'lead':role('serif-bold',138 if same else 209,22 if same else 25,143,269),'left':role('serif-bold',47,27,62,365),'right':role('serif-bold',47,27,217,365)}
 c['frameCount']=c['frames'];return c
def recipe(id,c,label):
 r=load(P/f'source/pilot/batches/circle/{id}-recipe.json');r['input']=f'source/pilot/detail-rest/circle/{id}-{label}.json'
 for ref in r['components'].values():ref['sha256']=sha(P/ref['source'])
 deps=['source/pilot/components/runtime.py','source/pilot/components/pairing.py','source/pilot/components/detail_tools.py','source/pilot/t04_render.py',r['input']]
 if id=='cg14':deps+=['source/pilot/detail-rest/circle/assets/warning-red.svg','source/pilot/detail-rest/circle/assets/warning-red.png']
 if id=='cg11':deps+=['source/pilot/detail-rest/circle/assets/torn-paper.svg','source/pilot/detail-rest/circle/assets/torn-paper.png']
 r['supportBindings']={path:sha(P/path) for path in deps};r['verificationState']='trial';r['completeGroupValidated']=False;r['purposeDocument']='source/pilot/detail-rest/circle/METHOD.md';return r
def encode(id,c,r,label):
 src=REF if label=='same' else SRC;start=c['referenceFrames'][0]/30 if label=='same' else c['rawRange'][0];N=c['frames'];out=O/f'{id}-{label}.mp4';validate_recipe(r)
 dec=subprocess.Popen(['ffmpeg','-v','error','-threads','2','-ss',str(start),'-i',src,'-frames:v',str(N),'-vf','fps=30,scale=286:508','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
 enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','286x508','-r','30','-i','pipe:0','-ss',str(start),'-i',src,'-map','0:v','-map','1:a:0','-t',str(N/30),'-vf','scale=572:1016:flags=lanczos','-c:v','libx264','-threads','2','-crf','15','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 for n in range(N):
  data=dec.stdout.read(286*508*3);assert len(data)==286*508*3;raw=Image.frombytes('RGB',(286,508),data);im=compose(r,raw,n,c);enc.stdin.write(im.convert('RGB').tobytes())
  if n in [0,6,round(N*.3),round(N*.6),N-1]:
   im.save(R/f'{id}-{label}-f{n:03d}.png')
   if label=='input':
    for key,layer in render_subtitle(c['subtitleFamily'],n,c).items():layer.save(R/f'{id}-{key}-f{n:03d}.png')
 enc.stdin.close();assert enc.wait()==0;assert dec.wait()==0;subprocess.run(['ffmpeg','-v','error','-threads','2','-i',str(out),'-f','null','-'],check=True);return out
def boards(id,c,s):
 cap=cv2.VideoCapture(str(O/f'{id}-same.mp4'));new=cv2.VideoCapture(str(O/f'{id}-input.mp4'));sheet=Image.new('RGB',(7*158,850),'#eeeee9');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',11)
 for j,f in enumerate(np.linspace(0,s['frames']-1,7,dtype=int)):
  original=Image.open(P/'observations/frame-audit/frames'/f'{s["referenceFrames"][0]+f+1:04d}.jpg').resize((143,254));sheet.paste(original,(j*158,20));d.text((j*158,2),f'原对标 f{f}',font=font,fill='#111')
  cap.set(cv2.CAP_PROP_POS_FRAMES,int(f));ok,a=cap.read();assert ok;sheet.paste(Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).resize((143,254)),(j*158,300));d.text((j*158,280),f'同字候选 f{f}',font=font,fill='#111')
  g=round(f/(s['frames']-1)*(c['frames']-1));new.set(cv2.CAP_PROP_POS_FRAMES,g);ok,a=new.read();assert ok;sheet.paste(Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).resize((143,254)),(j*158,580));d.text((j*158,560),f'迁移阶段 f{g}',font=font,fill='#111')
 cap.release();new.release();sheet.save(R/f'{id}-process.jpg',quality=93)
def main():
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe');page=b.new_page(device_scale_factor=4)
  for svg in (S/'assets').glob('*.svg'):
   page.set_content('<style>html,body{margin:0;background:transparent}</style>'+svg.read_text('utf-8'));page.locator('svg').screenshot(path=str(svg.with_suffix('.png')),omit_background=True)
  b.close()
 rows=[]
 for id in IDS:
  configs={}
  for label in ['same','input']:
   c=configure(id,label=='same');dump(S/f'{id}-{label}.json',c);r=recipe(id,c,label);dump(S/f'{id}-{label}-recipe.json',r);out=encode(id,c,r,label);configs[label]=c
  c=configs['input'];boards(id,c,configs['same']);rows.append({'occurrence':id,'name':old.SPECS[id]['name'],'file':(O/f'{id}-input.mp4').relative_to(P).as_posix(),'referenceFile':f'observations/accepted-review/{id}/reference-clip.mp4','recipe':f'source/pilot/detail-rest/circle/{id}-input-recipe.json','input':f'source/pilot/detail-rest/circle/{id}-input.json','frameCount':c['frames'],'rawRange':c['rawRange'],'sourceRange':[v/30 for v in c['referenceFrames']],'visualFamily':'v04','subtitleFamily':c['subtitleFamily'],'verificationState':'trial','sha256':sha(O/f'{id}-input.mp4'),'comparisonEvidence':f'reviews/detail-rest/circle/{id}-process.jpg','limitations':['字体为逐角色候选，原字体身份未确认','同字候选仅用成片人物圆窗测试，非拿到原源码/素材','原声效未独立重建，新口播词点未听审','尚待用户完整视觉检验']});dump(O/'manifest.json',{'groups':rows,'status':'03-detail-rework-trial-not-accepted'});print(id,rows[-1]['sha256'],flush=True)
 # cg13 layer hashes must remain byte-for-byte identical despite file hash change.
 frozen=load(R/'cg13-frozen-layer-hashes.json');c=load(P/'source/pilot/detail-two/cg13-input.json');actual={str(n):{k:sha_bytes(v.tobytes()) for k,v in render_subtitle('t09',n,c).items()} for n in range(c['frames'])};assert frozen==actual;dump(R/'cg13-regression.json',{'all76SubtitleFramesPixelIdentical':True,'mediaReencoded':False,'inputsChanged':False,'approvedMediaRemainsFrozen':True,'componentFileHashChangedRequiresTechnicalReceiptRecheck':True})
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
if __name__=='__main__':main()
