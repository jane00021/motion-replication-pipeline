from pathlib import Path
import sys,json,copy
P=Path(__file__).resolve().parents[4];sys.path.insert(0,str(P/'source/pilot'))
from batch_runtime import *
from components import text_tile
from PIL import Image,ImageDraw,ImageFont
from fontTools.ttLib import TTFont
import cv2,numpy as np
S=P/'source/pilot/batches/evidence';O=P/'render/pilot/batches/evidence';R=P/'reviews/pilot/batches/evidence';R.mkdir(exist_ok=True,parents=True)
catalog=load(P/'observations/group-catalog.json');font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',11)
checks=[];cal=[]
for row in load(O/'manifest.json')['groups']:
 id=row['occurrence'];c=load(P/row['input']);r=load(P/row['recipe']);validate(r);o=next(x for x in catalog['occurrences'] if x['id']==id);cap=cv2.VideoCapture(str(P/row['file']));sheet=Image.new('RGB',(6*146,570),'#eee');d=ImageDraw.Draw(sheet)
 for j,q in enumerate([0,.08,.25,.5,.75,.99]):
  sf=o['startFrame']+min(o['durationFrames']-1,round(q*(o['durationFrames']-1)));nf=min(c['frameCount']-1,round(q*(c['frameCount']-1)));im=Image.open(P/'observations/frame-audit/frames'/f'{sf+1:05d}.jpg');sheet.paste(im.convert('RGB').resize((142,252)),(j*146,20));d.text((j*146,2),f'参考 f{sf}',font=font,fill='#111');cap.set(cv2.CAP_PROP_POS_FRAMES,nf);ok,a=cap.read();assert ok;sheet.paste(Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).resize((142,252)),(j*146,300));d.text((j*146,280),f'新片阶段 f{nf}',font=font,fill='#111')
 cap.release();sheet.save(R/f'{id}-process.jpg',quality=93)
 # Same-word role images are honest static typography calibration, not full baseline.
 if id=='N06':pairs=[('工业时代',c['subtitle']['titleStyle']),('8小时工作制',c['subtitle']['goldStyle'])]
 elif id in ['N07','N14']:pairs=[('古人的睡觉',dict(font='D:/SKILL/font-check/SourceHanSerifSC-Bold.otf',size=25,fill='#fffef6')),('根据这一研究发现',dict(font='D:/SKILL/font-check/SourceHanSerifSC-Bold.otf',size=17,fill='#e4c64d'))]
 else:pairs=[('一次彻底的大扫除' if id=='N18' else '手术都像是虚脱了一样',dict(font='D:/SKILL/font-check/SourceHanSerifSC-Bold.otf',size=17,fill='#fffef6'))]
 board=Image.new('RGB',(520,140),'#263036');dd=ImageDraw.Draw(board)
 for j,(text,style) in enumerate(pairs):
  f=TTFont(style['font'],lazy=True);cmap=f.getBestCmap();f.close();assert all(ord(ch) in cmap for ch in text)
  tile,(w,h)=text_tile(text,json.dumps(style,sort_keys=True));board.paste(tile,(8,j*65),tile);cal.append({'occurrence':id,'sameWord':text,'style':style,'inkWidth':w,'inkHeight':h,'fontSha256':sha(style['font']),'scope':'static same-word candidate only; not same-clock full baseline'})
 board.save(R/f'{id}-same-word-font.png')
 # Actual parameter intervention on the same recipe/provider.
 n=c['frameCount']//2;raw=Image.new('RGB',(284,504),'#4b5962');a=compose(r,raw,n,c);change=copy.deepcopy(c)
 if id=='N06':change['subtitle']['title']='技能'
 elif id in ['N07','N14']:change['evidenceText']['documentTitle']='测试标题';n=max(n,c['events']['zoom'][1]+12);a=compose(r,raw,n,c)
 elif id=='N16':change['visual']['scale']=.75
 else:change['events']['ban']=[999,1000];n=c['events']['ban'][1]+2;a=compose(r,raw,n,c)
 b=compose(r,raw,n,change);assert not np.array_equal(a,b)
 checks.append({'occurrence':id,'parameterChangesPixels':True,'recipeSourceHashValid':True,'fullDecode':row['technical']['fullDecode'],'frames':row['frameCount'],'visualComponents':row['visualComponents'],'frameProcessEvidence':f'reviews/pilot/batches/evidence/{id}-process.jpg','sameWordFontEvidence':f'reviews/pilot/batches/evidence/{id}-same-word-font.png','continuousVisualPlayback':False,'audioListening':False,'userApproved':False})
dump(S/'font-calibration.json',cal);dump(R/'qa.json',{'groups':checks,'T04sharedOccurrences':['N07','N14'],'V14ReusedEntry':'components:visual','stageAccepted':False});print('evidence QA five complete groups')
