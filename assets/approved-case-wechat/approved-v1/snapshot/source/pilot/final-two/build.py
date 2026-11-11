from pathlib import Path
import sys,json,copy,subprocess,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'))
from components.common import core,load
from components.runtime import compose,validate_recipe
from components.detail_tools import glyph_tile
S=P/'source/pilot/final-two';O=P/'render/pilot/final-two';R=P/'reviews/final-two';O.mkdir(exist_ok=True)
fonts=load(P/'source/pilot/detail-two/fonts.json');src=load(P/'source/pilot/new-input/manifest.json')['path']
def sha(p):return core.file_sha(p)
def dump(p,v):core.dump(p,v)
def sty(key,w,h):return {'path':fonts[key],'size':64,'inkWidth':w,'inkHeight':h,'weightPx':.3,'fill':'#fffef8','shadow':{'dx':1.5,'dy':2,'blur':.25,'opacity':.9},'outlinePx':0}
c17=load(P/'source/pilot/batches/closing/cg17-input.json');c17.update(calibratedRoles=True,matteFrames='source/pilot/final-two/matte17')
c17['subtitle']['rows']=[{'text':'本事','glyphX':[1,190],'y':-1,'style':sty('youshe',83,76),'entry':3,'settle':12,'drift':-40,'skew':.06},{'text':'落地','glyphX':[-2,192],'y':149,'style':sty('youshe',86,72),'entry':5,'settle':14,'drift':32,'skew':.06}]
c17['subtitle']['captionStyle']=dict(sty('serif-bold',132,12),inkY=431)
c17['purpose']='与其空想，不如学个能落地的本事；整体缩入黑色舞台，巨字本事/落地分列人物两侧并在人与手后方，口播承担解释。'
c18=load(P/'source/pilot/batches/closing/cg18-input.json');c18.update(calibratedRoles=True)
for i,p in enumerate(c18['subtitle']['phrases']):p.update(style=sty('serif-heavy',22,23),tracking=1,rect=[12,282,99,40] if i==0 else [170,263,103,40])
c18['purpose']='踏实比求快更重要；画面恢复满屏后，左侧要踏实先落位，右侧别求快随后对照，逐字显形后留阅读时间。'
for oid,c in [('cg17',c17),('cg18',c18)]:
 c['sourceRange']=c['sourceFrames'];c['fps']=30;c['frames']=c['frameCount'];dump(S/f'{oid}-input.json',c)
 r=load(P/f'source/pilot/batches/closing/{oid}-recipe.json');r.update(input=f'source/pilot/final-two/{oid}-input.json',verificationState='trial',completeGroupValidated=False)
 for ref in r['components'].values():ref['sha256']=sha(P/ref['source'])
 deps=['source/pilot/components/common.py','source/pilot/components/detail_tools.py','source/pilot/components/runtime.py','source/pilot/components/pairing.py','source/pilot/t04_render.py',f'source/pilot/final-two/{oid}-input.json']
 if oid=='cg17':deps+=['source/pilot/final-two/matte17/manifest.json','source/pilot/final-two/matte.py','source/pilot/detail-rest/scene/models/rvm.onnx']
 r['supportBindings']={d:sha(P/d) for d in deps};dump(S/f'{oid}-recipe.json',r);validate_recipe(r)
 N=c['frameCount'];fp=O/f'{oid}.mp4';dec=subprocess.Popen(['ffmpeg','-v','error','-ss',str(c['rawRange'][0]),'-i',src,'-frames:v',str(N),'-vf','fps=30,scale=286:508','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
 enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-s','286x508','-pix_fmt','rgb24','-r','30','-i','pipe:0','-ss',str(c['rawRange'][0]),'-i',src,'-t',str(N/30),'-map','0:v','-map','1:a:0','-vf','scale=572:1016:flags=lanczos','-c:v','libx264','-threads','2','-crf','15','-preset','fast','-c:a','aac','-pix_fmt','yuv420p','-movflags','+faststart',str(fp)],stdin=subprocess.PIPE)
 for n in range(N):
  data=dec.stdout.read(286*508*3);assert len(data)==286*508*3;raw=Image.frombytes('RGB',(286,508),data);im=compose(r,raw,n,c);enc.stdin.write(im.convert('RGB').tobytes())
  if n in [0,3,8,15,N//2,N-6,N-1]:im.save(R/f'{oid}-{n:03d}.png')
 enc.stdin.close();assert enc.wait()==dec.wait()==0;subprocess.run(['ffmpeg','-v','error','-i',str(fp),'-f','null','-'],check=True)
 print(oid,sha(fp),flush=True)
# Same-word role comparison; source pixels only for evidence, never in glyph rendering.
board=Image.new('RGB',(1000,420),'#293540');d=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
ref=Image.open(P/'observations/frame-audit/frames/1120.jpg');board.paste(ref.resize((172,305)),(5,28));d.text((5,5),'17 原片字形',font=font,fill='white')
for j,key in enumerate(['sans-bold','youshe']):
 sample=Image.new('RGBA',(286,310),'#303b42')
 for row,txt in enumerate(['认知','筛选']):
  for k,ch in enumerate(txt):
   im,bb=glyph_tile(ch,json.dumps(sty(key,83,76),sort_keys=True));sample.alpha_composite(im,(2+190*k,10+row*149))
 board.paste(sample.convert('RGB'),(200+j*300,28));d.text((200+j*300,5),key+' 同字候选',font=font,fill='white')
ref=Image.open(P/'observations/frame-audit/frames/1155.jpg');board.paste(ref.crop((0,260,286,335)).resize((286,75)),(5,340));d.text((310,350),'18：宋体候选，3字逐字入场，按全句字面居中',font=font,fill='white')
board.save(R/'same-word-calibration.jpg')
